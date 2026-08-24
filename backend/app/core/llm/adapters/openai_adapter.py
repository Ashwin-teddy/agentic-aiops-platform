from __future__ import annotations

from typing import TYPE_CHECKING, Any

from openai import AsyncOpenAI

from app.core.config.settings import settings
from app.core.llm.adapters.base import BaseEmbeddingAdapter, BaseLLMAdapter
from app.core.llm.types import (
    EmbeddingResult,
    LLMMessage,
    LLMResponse,
    LLMUsage,
    ModelConfig,
    ModelProvider,
)
from app.observability.logging import get_logger

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

logger = get_logger(__name__)


class OpenAIAdapter(BaseLLMAdapter):
    def __init__(self, config: ModelConfig) -> None:
        super().__init__(config)
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            organization=settings.openai_org_id or None,
        )

    async def chat(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.1,
        max_tokens: int | None = None,
        json_mode: bool = False,
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        api_messages = [{"role": m.role, "content": m.content} for m in messages]
        params: dict[str, Any] = {
            "model": self.model_id,
            "messages": api_messages,
            "temperature": temperature,
            "max_tokens": max_tokens or self.config.max_tokens,
        }
        if json_mode and self.config.supports_json_mode:
            params["response_format"] = {"type": "json_object"}
        if tools and self.config.supports_tools:
            params["tools"] = tools
            params["tool_choice"] = "auto"
        response = await self.client.chat.completions.create(**params)
        choice = response.choices[0]
        usage = LLMUsage(
            prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
            completion_tokens=response.usage.completion_tokens if response.usage else 0,
            total_tokens=response.usage.total_tokens if response.usage else 0,
        )
        usage.cost_usd = self._calculate_cost(usage)
        tool_calls = []
        if choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                tool_calls.append(
                    {
                        "id": tc.id,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                )
        return LLMResponse(
            content=choice.message.content or "",
            model=response.model,
            provider=ModelProvider.OPENAI,
            usage=usage,
            finish_reason=choice.finish_reason or "",
            tool_calls=tool_calls,
        )

    async def chat_stream(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.1,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        api_messages = [{"role": m.role, "content": m.content} for m in messages]
        stream = await self.client.chat.completions.create(
            model=self.model_id,
            messages=api_messages,
            temperature=temperature,
            max_tokens=max_tokens or self.config.max_tokens,
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def health_check(self) -> bool:
        try:
            await self.client.models.retrieve(self.model_id)
            return True
        except Exception:
            return False


class OpenAIEmbeddingAdapter(BaseEmbeddingAdapter):
    def __init__(self, config: ModelConfig) -> None:
        super().__init__(config)
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            organization=settings.openai_org_id or None,
        )

    async def embed_texts(self, texts: list[str]) -> EmbeddingResult:
        all_embeddings: list[list[float]] = []
        batch_size = 100
        total_tokens = 0
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            response = await self.client.embeddings.create(
                model=self.model_id,
                input=batch,
                dimensions=self.dimensions,
            )
            all_embeddings.extend([item.embedding for item in response.data])
            total_tokens += response.usage.total_tokens
        usage = LLMUsage(prompt_tokens=total_tokens, total_tokens=total_tokens)
        return EmbeddingResult(
            embeddings=all_embeddings,
            model=self.model_id,
            provider=ModelProvider.OPENAI,
            dimensions=self.dimensions,
            usage=usage,
        )

    async def health_check(self) -> bool:
        try:
            await self.client.embeddings.create(model=self.model_id, input=["test"])
            return True
        except Exception:
            return False
