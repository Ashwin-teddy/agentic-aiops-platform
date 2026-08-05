from __future__ import annotations

import time
from typing import Any

from app.core.llm.adapters.base import BaseLLMAdapter
from app.core.llm.adapters.openai_adapter import OpenAIAdapter
from app.core.llm.adapters.anthropic_adapter import AnthropicAdapter
from app.core.llm.adapters.gemini_adapter import GeminiAdapter
from app.core.llm.adapters.ollama_adapter import OllamaAdapter
from app.core.llm.types import (
    LLMMessage,
    LLMResponse,
    LLMUsage,
    ModelConfig,
    ModelProvider,
    TaskType,
    AVAILABLE_MODELS,
    TASK_MODEL_ROUTING,
    apply_environment_overrides,
)
from app.observability.logging import get_logger
from app.observability.metrics import LLM_TOKENS_USED
from app.core.config.settings import settings

logger = get_logger(__name__)


class ModelRouter:
    def __init__(self, fallback_enabled: bool = True) -> None:
        apply_environment_overrides(settings.ollama_base_url)
        self._adapters: dict[str, BaseLLMAdapter] = {}
        self._task_overrides: dict[TaskType, str] = {}
        self._fallback_enabled = fallback_enabled
        self._default_model: str = "llama3.2"

    def _get_or_create_adapter(self, model_key: str) -> BaseLLMAdapter:
        if model_key not in self._adapters:
            config = AVAILABLE_MODELS.get(model_key)
            if not config:
                raise ValueError(f"Unknown model: {model_key}")
            self._adapters[model_key] = self._create_adapter(config)
        return self._adapters[model_key]

    def _create_adapter(self, config: ModelConfig) -> BaseLLMAdapter:
        if config.provider == ModelProvider.OPENAI:
            return OpenAIAdapter(config)
        elif config.provider == ModelProvider.ANTHROPIC:
            return AnthropicAdapter(config)
        elif config.provider == ModelProvider.GOOGLE:
            return GeminiAdapter(config)
        elif config.provider == ModelProvider.OLLAMA:
            return OllamaAdapter(config)
        raise ValueError(f"Unsupported provider: {config.provider}")

    def set_task_model(self, task: TaskType, model_key: str) -> None:
        if model_key not in AVAILABLE_MODELS:
            raise ValueError(f"Unknown model: {model_key}")
        self._task_overrides[task] = model_key
        logger.info("task_model_override", task=task.value, model=model_key)

    def set_default_model(self, model_key: str) -> None:
        if model_key not in AVAILABLE_MODELS:
            raise ValueError(f"Unknown model: {model_key}")
        self._default_model = model_key

    def get_model_for_task(self, task: TaskType, tier_preference: str | None = None) -> str:
        if task in self._task_overrides:
            return self._task_overrides[task]
        candidates = TASK_MODEL_ROUTING.get(task, [self._default_model])
        if tier_preference:
            tier_filtered = [
                k for k in candidates
                if AVAILABLE_MODELS.get(k) and AVAILABLE_MODELS[k].tier.value == tier_preference
            ]
            if tier_filtered:
                return tier_filtered[0]
        return candidates[0]

    async def chat(
        self,
        messages: list[LLMMessage],
        model: str | None = None,
        task: TaskType = TaskType.GENERAL,
        temperature: float = 0.1,
        max_tokens: int | None = None,
        json_mode: bool = False,
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        model_key = model or self.get_model_for_task(task)
        adapter = self._get_or_create_adapter(model_key)
        try:
            response = await adapter.safe_chat(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                json_mode=json_mode,
                tools=tools,
            )
            LLM_TOKENS_USED.labels(model=model_key).inc(response.usage.total_tokens)
            return response
        except Exception as e:
            if self._fallback_enabled and model is None:
                logger.warning("llm_primary_failed", model=model_key, error=str(e))
                fallback_key = self._get_fallback(model_key)
                if fallback_key and fallback_key != model_key:
                    logger.info("llm_fallback", from_model=model_key, to_model=fallback_key)
                    fallback_adapter = self._get_or_create_adapter(fallback_key)
                    return await fallback_adapter.safe_chat(
                        messages=messages, temperature=temperature,
                        max_tokens=max_tokens, json_mode=json_mode,
                    )
            raise

    async def chat_stream(
        self,
        messages: list[LLMMessage],
        model: str | None = None,
        task: TaskType = TaskType.GENERAL,
        temperature: float = 0.1,
        max_tokens: int | None = None,
        **kwargs: Any,
    ):
        model_key = model or self.get_model_for_task(task)
        adapter = self._get_or_create_adapter(model_key)
        async for chunk in adapter.chat_stream(
            messages=messages, temperature=temperature, max_tokens=max_tokens,
        ):
            yield chunk

    def _get_fallback(self, failed_model: str) -> str | None:
        failed_config = AVAILABLE_MODELS.get(failed_model)
        if not failed_config:
            return None
        for key, config in AVAILABLE_MODELS.items():
            if key != failed_model and config.provider == failed_config.provider and config.tier == failed_config.tier:
                return key
        for key, config in AVAILABLE_MODELS.items():
            if key != failed_model and config.tier == failed_config.tier:
                return key
        return self._default_model

    async def health_check_all(self) -> dict[str, bool]:
        results: dict[str, bool] = {}
        checked: set[ModelProvider] = set()
        for key, config in AVAILABLE_MODELS.items():
            if config.provider in checked:
                continue
            checked.add(config.provider)
            try:
                adapter = self._get_or_create_adapter(key)
                results[config.display_name] = await adapter.health_check()
            except Exception:
                results[config.display_name] = False
        return results

    def list_models(self) -> list[dict[str, Any]]:
        return [
            {
                "key": k,
                "provider": v.provider.value,
                "display_name": v.display_name,
                "tier": v.tier.value,
                "context_window": v.context_window,
                "max_tokens": v.max_tokens,
                "cost_per_million_input": v.input_cost_per_million,
                "cost_per_million_output": v.output_cost_per_million,
                "supports_tools": v.supports_tools,
                "supports_vision": v.supports_vision,
            }
            for k, v in AVAILABLE_MODELS.items()
        ]

    def get_task_routing(self) -> dict[str, list[str]]:
        return {task.value: models for task, models in TASK_MODEL_ROUTING.items()}


_model_router: ModelRouter | None = None


def get_model_router() -> ModelRouter:
    global _model_router
    if _model_router is None:
        _model_router = ModelRouter()
    return _model_router
