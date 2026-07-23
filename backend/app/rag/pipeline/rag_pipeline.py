from __future__ import annotations

from typing import Any

from app.core.config.settings import settings
from app.core.llm.router import get_model_router
from app.core.llm.types import LLMMessage, TaskType
from app.rag.retrieval.retriever import RAGRetriever
from app.observability.logging import get_logger

logger = get_logger(__name__)


class RAGPipeline:
    def __init__(self) -> None:
        self.retriever = RAGRetriever()
        self.router = get_model_router()

    async def query(
        self,
        question: str,
        top_k: int = 5,
        source_filter: str | None = None,
        system_prompt: str | None = None,
        model: str | None = None,
    ) -> dict[str, Any]:
        results = await self.retriever.retrieve(question, top_k=top_k, source_filter=source_filter)
        formatted = self.retriever.format_with_citations(results)
        default_system = (
            "You are an enterprise IT operations assistant. Answer based on the provided context. "
            "Always cite your sources using [N] notation. If the context doesn't contain enough "
            "information, say so explicitly. Be precise and actionable."
        )
        messages = [
            LLMMessage(role="system", content=system_prompt or default_system),
            LLMMessage(role="user", content=f"Context:\n{formatted['answer_context']}\n\nQuestion: {question}"),
        ]
        response = await self.router.chat(
            messages=messages,
            task=TaskType.RAG_ANSWER,
            model=model or settings.default_rag_model or None,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
        )
        return {
            "answer": response.content,
            "citations": formatted["citations"],
            "sources_used": len(results),
            "model": response.model,
            "provider": response.provider.value,
            "tokens_used": response.usage.total_tokens,
            "cost_usd": response.usage.cost_usd,
        }


_rag_pipeline: RAGPipeline | None = None


def get_rag_pipeline() -> RAGPipeline:
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = RAGPipeline()
    return _rag_pipeline
