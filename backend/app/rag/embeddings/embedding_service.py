from __future__ import annotations

from typing import Any

from app.core.llm.embeddings.embedding_router import get_embedding_router
from app.core.llm.types import EmbeddingResult
from app.observability.logging import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    def __init__(self, model: str | None = None) -> None:
        self.router = get_embedding_router()
        self.model = model

    async def embed_text(self, text: str) -> list[float]:
        return await self.router.embed_single(text, model_key=self.model)

    async def embed_batch(self, texts: list[str], batch_size: int = 100) -> list[list[float]]:
        all_embeddings: list[list[float]] = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            result = await self.router.embed(batch, model_key=self.model)
            all_embeddings.extend(result.embeddings)
            logger.info("embeddings_batch", batch_start=i, batch_size=len(batch))
        return all_embeddings

    async def embed_with_metadata(self, texts: list[str]) -> EmbeddingResult:
        return await self.router.embed(texts, model_key=self.model)
