from __future__ import annotations

from typing import Any

from app.core.config.settings import settings
from app.observability.logging import get_logger
from app.rag.embeddings.embedding_service import EmbeddingService
from app.rag.vector_store.qdrant_store import QdrantVectorStore

logger = get_logger(__name__)


class RAGRetriever:
    def __init__(self) -> None:
        self.embedding_service = EmbeddingService()
        self.vector_store = QdrantVectorStore()

    async def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        score_threshold: float | None = None,
        source_filter: str | None = None,
    ) -> list[dict[str, Any]]:
        top_k = top_k or settings.rag_top_k
        score_threshold = score_threshold or settings.rag_similarity_threshold
        query_embedding = await self.embedding_service.embed_text(query)
        try:
            results = await self.vector_store.search(
                query_embedding=query_embedding,
                top_k=top_k,
                score_threshold=score_threshold,
                source_filter=source_filter,
            )
        except Exception as e:
            logger.warning("rag_retrieval_failed", error=str(e), fallback="empty_results")
            results = []
        logger.info("rag_retrieval", query_length=len(query), results_count=len(results))
        return results

    def format_context(self, results: list[dict[str, Any]]) -> str:
        if not results:
            return "No relevant knowledge found."
        context_parts = []
        for i, r in enumerate(results, 1):
            source = r.get("source", "unknown")
            title = r.get("title", "Untitled")
            content = r.get("content", "")
            score = r.get("score", 0)
            context_parts.append(
                f"[{i}] Source: {source} | Title: {title} | Relevance: {score:.2f}\n{content}"
            )
        return "\n\n---\n\n".join(context_parts)

    def format_with_citations(self, results: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "answer_context": self.format_context(results),
            "citations": [
                {
                    "index": i,
                    "title": r.get("title", ""),
                    "source": r.get("source", ""),
                    "source_url": r.get("source_url", ""),
                    "score": r.get("score", 0),
                }
                for i, r in enumerate(results, 1)
            ],
        }
