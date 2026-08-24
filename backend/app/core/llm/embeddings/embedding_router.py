from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.core.config.settings import settings
from app.core.llm.adapters.ollama_adapter import OllamaEmbeddingAdapter
from app.core.llm.adapters.openai_adapter import OpenAIEmbeddingAdapter
from app.core.llm.types import (
    AVAILABLE_MODELS,
    ModelConfig,
    ModelProvider,
    apply_environment_overrides,
)
from app.observability.logging import get_logger

if TYPE_CHECKING:
    from app.core.llm.adapters.base import BaseEmbeddingAdapter

logger = get_logger(__name__)


class EmbeddingRouter:
    def __init__(self) -> None:
        apply_environment_overrides(settings.ollama_base_url)
        self._adapters: dict[str, BaseEmbeddingAdapter] = {}
        self._default_model: str = settings.default_embedding_model

    def _get_or_create(self, model_key: str) -> BaseEmbeddingAdapter:
        if model_key not in self._adapters:
            config = AVAILABLE_MODELS.get(model_key)
            if not config:
                raise ValueError(f"Unknown embedding model: {model_key}")
            self._adapters[model_key] = self._create_adapter(config)
        return self._adapters[model_key]

    def _create_adapter(self, config: ModelConfig) -> BaseEmbeddingAdapter:
        if config.provider == ModelProvider.OPENAI:
            return OpenAIEmbeddingAdapter(config)
        if config.provider == ModelProvider.OLLAMA:
            return OllamaEmbeddingAdapter(config)
        raise ValueError(f"Embedding not supported for provider: {config.provider}")

    def set_default(self, model_key: str) -> None:
        if model_key not in AVAILABLE_MODELS:
            raise ValueError(f"Unknown model: {model_key}")
        self._default_model = model_key

    async def embed(self, texts: list[str], model_key: str | None = None) -> Any:
        key = model_key or self._default_model
        adapter = self._get_or_create(key)
        return await adapter.safe_embed(texts)

    async def embed_single(self, text: str, model_key: str | None = None) -> list[float]:
        result = await self.embed([text], model_key)
        return result.embeddings[0]

    def get_dimensions(self, model_key: str | None = None) -> int:
        key = model_key or self._default_model
        config = AVAILABLE_MODELS.get(key)
        return config.embedding_dims if config else 3072

    def list_models(self) -> list[dict[str, Any]]:
        return [
            {"key": k, "display_name": v.display_name, "dimensions": v.embedding_dims}
            for k, v in AVAILABLE_MODELS.items()
            if v.tier.value == "embedding"
        ]


_embedding_router: EmbeddingRouter | None = None


def get_embedding_router() -> EmbeddingRouter:
    global _embedding_router
    if _embedding_router is None:
        _embedding_router = EmbeddingRouter()
    return _embedding_router
