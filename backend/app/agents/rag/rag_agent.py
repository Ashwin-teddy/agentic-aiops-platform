from __future__ import annotations

from app.rag.pipeline.rag_pipeline import RAGPipeline, get_rag_pipeline
from app.rag.retrieval.retriever import RAGRetriever
from app.observability.logging import get_logger

logger = get_logger(__name__)


class RAGAgent:
    name = "rag_agent"

    def __init__(self) -> None:
        self.pipeline = get_rag_pipeline()
        self.retriever = RAGRetriever()

    async def search_knowledge(
        self,
        query: str,
        top_k: int = 5,
        source_filter: str | None = None,
        generate_answer: bool = True,
    ) -> dict:
        results = await self.retriever.retrieve(query, top_k=top_k, source_filter=source_filter)
        response = {"results": results, "citations": [], "answer": None}
        if results:
            formatted = self.retriever.format_with_citations(results)
            response["citations"] = formatted["citations"]
        if generate_answer:
            llm_response = await self.pipeline.query(query, top_k=top_k, source_filter=source_filter)
            response["answer"] = llm_response.get("answer", "")
            response["tokens_used"] = llm_response.get("tokens_used", 0)
        logger.info("rag_search_complete", query_length=len(query), results=len(results))
        return response

    async def search_runbooks(self, service: str, issue_description: str) -> dict:
        query = f"runbook for {service}: {issue_description}"
        return await self.search_knowledge(query, source_filter="runbook")

    async def search_similar_incidents(self, description: str) -> dict:
        query = f"similar incident: {description}"
        return await self.search_knowledge(query, source_filter="incident_report")

    async def search_sop(self, procedure_name: str) -> dict:
        query = f"standard operating procedure: {procedure_name}"
        return await self.search_knowledge(query, source_filter="sop")
