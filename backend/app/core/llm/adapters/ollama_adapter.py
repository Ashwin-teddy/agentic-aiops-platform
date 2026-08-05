from __future__ import annotations

import json
from typing import Any, AsyncGenerator

import httpx

from app.core.llm.adapters.base import BaseLLMAdapter, BaseEmbeddingAdapter
from app.core.llm.types import (
    LLMMessage,
    LLMResponse,
    LLMUsage,
    EmbeddingResult,
    ModelConfig,
    ModelProvider,
)
from app.observability.logging import get_logger

logger = get_logger(__name__)


class OllamaAdapter(BaseLLMAdapter):
    def __init__(self, config: ModelConfig) -> None:
        super().__init__(config)
        self.base_url = config.base_url or "http://localhost:11434"
        self.headers = {"ngrok-skip-browser-warning": "true"}

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
        payload: dict[str, Any] = {
            "model": self.model_id,
            "messages": api_messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens or self.config.max_tokens,
            },
        }
        if json_mode:
            payload["format"] = "json"
        if tools and self.config.supports_tools:
            ollama_tools = []
            for t in tools:
                ollama_tools.append({
                    "type": "function",
                    "function": {
                        "name": t.get("name", ""),
                        "description": t.get("description", ""),
                        "parameters": t.get("parameters", {"type": "object", "properties": {}}),
                    },
                })
            payload["tools"] = ollama_tools
        async with httpx.AsyncClient(timeout=300) as client:
            response = await client.post(f"{self.base_url}/api/chat", json=payload, headers=self.headers)
            response.raise_for_status()
            data = response.json()
        message = data.get("message", {})
        content = message.get("content", "")
        tool_calls = []
        if message.get("tool_calls"):
            for tc in message["tool_calls"]:
                func = tc.get("function", {})
                tool_calls.append({
                    "id": f"call_{func.get('name', 'unknown')}",
                    "function": {
                        "name": func.get("name", ""),
                        "arguments": json.dumps(func.get("arguments", {})),
                    },
                })
        usage_data = data.get("prompt_eval_count", 0)
        completion_tokens = data.get("eval_count", 0)
        usage = LLMUsage(
            prompt_tokens=usage_data,
            completion_tokens=completion_tokens,
            total_tokens=usage_data + completion_tokens,
        )
        usage.cost_usd = 0.0
        return LLMResponse(
            content=content,
            model=self.model_id,
            provider=ModelProvider.OLLAMA,
            usage=usage,
            finish_reason="stop",
            tool_calls=tool_calls,
            metadata={"total_duration_ns": data.get("total_duration", 0)},
        )

    async def chat_stream(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.1,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        api_messages = [{"role": m.role, "content": m.content} for m in messages]
        payload = {
            "model": self.model_id,
            "messages": api_messages,
            "stream": True,
            "options": {"temperature": temperature, "num_predict": max_tokens or self.config.max_tokens},
        }
        async with httpx.AsyncClient(timeout=300) as client:
            async with client.stream("POST", f"{self.base_url}/api/chat", json=payload, headers=self.headers) as response:
                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            chunk = json.loads(line)
                            if chunk.get("message", {}).get("content"):
                                yield chunk["message"]["content"]
                        except json.JSONDecodeError:
                            continue

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.base_url}/api/tags", headers=self.headers)
                return response.status_code == 200
        except Exception:
            return False


class OllamaEmbeddingAdapter(BaseEmbeddingAdapter):
    def __init__(self, config: ModelConfig) -> None:
        super().__init__(config)
        self.base_url = config.base_url or "http://localhost:11434"
        self.headers = {"ngrok-skip-browser-warning": "true"}

    async def embed_texts(self, texts: list[str]) -> EmbeddingResult:
        payload = {
            "model": self.model_id,
            "input": texts,
        }
        async with httpx.AsyncClient(timeout=300) as client:
            response = await client.post(f"{self.base_url}/api/embed", json=payload, headers=self.headers)
            response.raise_for_status()
            data = response.json()
        embeddings = data.get("embeddings", [])
        total_tokens = sum(len(t.split()) for t in texts)
        usage = LLMUsage(prompt_tokens=total_tokens, total_tokens=total_tokens, cost_usd=0.0)
        return EmbeddingResult(
            embeddings=embeddings,
            model=self.model_id,
            provider=ModelProvider.OLLAMA,
            dimensions=self.dimensions or (len(embeddings[0]) if embeddings else 0),
            usage=usage,
        )

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.base_url}/api/tags", headers=self.headers)
                return response.status_code == 200
        except Exception:
            return False
