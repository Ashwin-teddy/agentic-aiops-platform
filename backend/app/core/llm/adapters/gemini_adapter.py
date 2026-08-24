from __future__ import annotations

from typing import TYPE_CHECKING, Any

from google import genai
from google.genai import types as gemini_types

from app.core.config.settings import settings
from app.core.llm.adapters.base import BaseLLMAdapter
from app.core.llm.types import (
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


class GeminiAdapter(BaseLLMAdapter):
    def __init__(self, config: ModelConfig) -> None:
        super().__init__(config)
        self.client = genai.Client(api_key=settings.google_api_key)

    async def chat(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.1,
        max_tokens: int | None = None,
        json_mode: bool = False,
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        system_instruction = ""
        contents = []
        for m in messages:
            if m.role == "system":
                system_instruction = m.content
            else:
                role = "user" if m.role == "user" else "model"
                contents.append(
                    gemini_types.Content(
                        role=role,
                        parts=[gemini_types.Part.from_text(text=m.content)],
                    )
                )
        if not contents:
            contents = [
                gemini_types.Content(role="user", parts=[gemini_types.Part.from_text(text="Hello")])
            ]
        config = gemini_types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens or self.config.max_tokens,
        )
        if system_instruction:
            config.system_instruction = system_instruction
        if json_mode:
            config.response_mime_type = "application/json"
        response = self.client.models.generate_content(
            model=self.model_id,
            contents=contents,
            config=config,
        )
        content = response.text or ""
        usage_data = response.usage_metadata
        usage = LLMUsage(
            prompt_tokens=getattr(usage_data, "prompt_token_count", 0) or 0,
            completion_tokens=getattr(usage_data, "candidates_token_count", 0) or 0,
            total_tokens=getattr(usage_data, "total_token_count", 0) or 0,
        )
        usage.cost_usd = self._calculate_cost(usage)
        return LLMResponse(
            content=content,
            model=self.model_id,
            provider=ModelProvider.GOOGLE,
            usage=usage,
            finish_reason=getattr(response.candidates[0], "finish_reason", "")
            if response.candidates
            else "",
        )

    async def chat_stream(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.1,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        system_instruction = ""
        contents = []
        for m in messages:
            if m.role == "system":
                system_instruction = m.content
            else:
                role = "user" if m.role == "user" else "model"
                contents.append(
                    gemini_types.Content(
                        role=role,
                        parts=[gemini_types.Part.from_text(text=m.content)],
                    )
                )
        config = gemini_types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens or self.config.max_tokens,
        )
        if system_instruction:
            config.system_instruction = system_instruction
        for chunk in self.client.models.generate_content_stream(
            model=self.model_id,
            contents=contents,
            config=config,
        ):
            if chunk.text:
                yield chunk.text

    async def health_check(self) -> bool:
        try:
            self.client.models.generate_content(
                model=self.model_id,
                contents=[
                    gemini_types.Content(
                        role="user", parts=[gemini_types.Part.from_text(text="ping")]
                    )
                ],
                config=gemini_types.GenerateContentConfig(max_output_tokens=10),
            )
            return True
        except Exception:
            return False
