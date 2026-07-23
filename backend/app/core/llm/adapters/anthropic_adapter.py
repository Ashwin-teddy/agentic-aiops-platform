from __future__ import annotations

import json
from typing import Any, AsyncGenerator

import httpx

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

logger = get_logger(__name__)


class AnthropicAdapter(BaseLLMAdapter):
    def __init__(self, config: ModelConfig) -> None:
        super().__init__(config)
        self.api_key = settings.anthropic_api_key
        self.base_url = "https://api.anthropic.com/v1"
        self.headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

    async def chat(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.1,
        max_tokens: int | None = None,
        json_mode: bool = False,
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        system_message = ""
        api_messages = []
        for m in messages:
            if m.role == "system":
                system_message = m.content
            else:
                api_messages.append({"role": m.role, "content": m.content})
        if not api_messages:
            api_messages = [{"role": "user", "content": "Hello"}]
        payload: dict[str, Any] = {
            "model": self.model_id,
            "messages": api_messages,
            "max_tokens": max_tokens or self.config.max_tokens,
            "temperature": temperature,
        }
        if system_message:
            payload["system"] = system_message
        if json_mode:
            payload["system"] = (payload.get("system", "") + "\nRespond with valid JSON only.").strip()
        if tools and self.config.supports_tools:
            anthropic_tools = []
            for t in tools:
                anthropic_tools.append({
                    "name": t.get("name", ""),
                    "description": t.get("description", ""),
                    "input_schema": t.get("parameters", {"type": "object", "properties": {}}),
                })
            payload["tools"] = anthropic_tools
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{self.base_url}/messages",
                headers=self.headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
        content = ""
        tool_calls = []
        for block in data.get("content", []):
            if block["type"] == "text":
                content += block["text"]
            elif block["type"] == "tool_use":
                tool_calls.append({
                    "id": block["id"],
                    "function": {
                        "name": block["name"],
                        "arguments": json.dumps(block["input"]),
                    },
                })
        usage_data = data.get("usage", {})
        usage = LLMUsage(
            prompt_tokens=usage_data.get("input_tokens", 0),
            completion_tokens=usage_data.get("output_tokens", 0),
            total_tokens=usage_data.get("input_tokens", 0) + usage_data.get("output_tokens", 0),
        )
        usage.cost_usd = self._calculate_cost(usage)
        return LLMResponse(
            content=content,
            model=data.get("model", self.model_id),
            provider=ModelProvider.ANTHROPIC,
            usage=usage,
            finish_reason=data.get("stop_reason", ""),
            tool_calls=tool_calls,
        )

    async def chat_stream(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.1,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        system_message = ""
        api_messages = []
        for m in messages:
            if m.role == "system":
                system_message = m.content
            else:
                api_messages.append({"role": m.role, "content": m.content})
        payload: dict[str, Any] = {
            "model": self.model_id,
            "messages": api_messages,
            "max_tokens": max_tokens or self.config.max_tokens,
            "temperature": temperature,
            "stream": True,
        }
        if system_message:
            payload["system"] = system_message
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST", f"{self.base_url}/messages",
                headers=self.headers, json=payload,
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        try:
                            event = json.loads(data_str)
                            if event.get("type") == "content_block_delta":
                                delta = event.get("delta", {})
                                if delta.get("type") == "text_delta":
                                    yield delta.get("text", "")
                        except json.JSONDecodeError:
                            continue

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers=self.headers,
                )
                return response.status_code == 200
        except Exception:
            return False
