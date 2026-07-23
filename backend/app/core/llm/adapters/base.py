from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from typing import Any

from app.core.llm.types import (
    LLMMessage,
    LLMResponse,
    LLMUsage,
    EmbeddingResult,
    ModelConfig,
    ModelProvider,
)
from app.core.security.encryption import mask_pii
from app.observability.logging import get_logger

logger = get_logger(__name__)


class BaseLLMAdapter(ABC):
    def __init__(self, config: ModelConfig) -> None:
        self.config = config
        self.provider = config.provider
        self.model_id = config.model_id

    @abstractmethod
    async def chat(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.1,
        max_tokens: int | None = None,
        json_mode: bool = False,
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        ...

    @abstractmethod
    async def chat_stream(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.1,
        max_tokens: int | None = None,
        **kwargs: Any,
    ):
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        ...

    async def safe_chat(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.1,
        max_tokens: int | None = None,
        json_mode: bool = False,
        **kwargs: Any,
    ) -> LLMResponse:
        start = time.monotonic()
        try:
            response = await self.chat(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                json_mode=json_mode,
                **kwargs,
            )
            elapsed_ms = (time.monotonic() - start) * 1000
            response.latency_ms = elapsed_ms
            logger.info(
                "llm_call_completed",
                provider=self.provider.value,
                model=self.model_id,
                tokens=response.usage.total_tokens,
                latency_ms=round(elapsed_ms, 2),
                cost_usd=response.usage.cost_usd,
            )
            return response
        except Exception as e:
            elapsed_ms = (time.monotonic() - start) * 1000
            logger.error(
                "llm_call_failed",
                provider=self.provider.value,
                model=self.model_id,
                error=str(e),
                latency_ms=round(elapsed_ms, 2),
            )
            raise

    def _calculate_cost(self, usage: LLMUsage) -> float:
        input_cost = (usage.prompt_tokens / 1_000_000) * self.config.input_cost_per_million
        output_cost = (usage.completion_tokens / 1_000_000) * self.config.output_cost_per_million
        return round(input_cost + output_cost, 6)

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider.value,
            "model_id": self.model_id,
            "display_name": self.config.display_name,
            "tier": self.config.tier.value,
            "context_window": self.config.context_window,
            "max_tokens": self.config.max_tokens,
            "supports_tools": self.config.supports_tools,
            "supports_json_mode": self.config.supports_json_mode,
        }


class BaseEmbeddingAdapter(ABC):
    def __init__(self, config: ModelConfig) -> None:
        self.config = config
        self.provider = config.provider
        self.model_id = config.model_id
        self.dimensions = config.embedding_dims

    @abstractmethod
    async def embed_texts(self, texts: list[str]) -> EmbeddingResult:
        ...

    async def embed_single(self, text: str) -> list[float]:
        result = await self.embed_texts([text])
        return result.embeddings[0]

    @abstractmethod
    async def health_check(self) -> bool:
        ...

    async def safe_embed(self, texts: list[str]) -> EmbeddingResult:
        start = time.monotonic()
        try:
            result = await self.embed_texts(texts)
            elapsed_ms = (time.monotonic() - start) * 1000
            logger.info(
                "embedding_completed",
                provider=self.provider.value,
                model=self.model_id,
                count=len(texts),
                latency_ms=round(elapsed_ms, 2),
            )
            return result
        except Exception as e:
            elapsed_ms = (time.monotonic() - start) * 1000
            logger.error(
                "embedding_failed",
                provider=self.provider.value,
                model=self.model_id,
                error=str(e),
            )
            raise
