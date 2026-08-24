from __future__ import annotations

from typing import Any

from app.observability.logging import get_logger

logger = get_logger(__name__)


class DocumentChunker:
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_text(self, text: str, metadata: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        chunks = []
        start = 0
        chunk_index = 0
        while start < len(text):
            end = start + self.chunk_size
            chunk_text = text[start:end]
            if end < len(text):
                last_period = chunk_text.rfind(".")
                last_newline = chunk_text.rfind("\n")
                split_point = max(last_period, last_newline)
                if split_point > self.chunk_size // 2:
                    end = start + split_point + 1
                    chunk_text = text[start:end]
            chunks.append(
                {
                    "content": chunk_text.strip(),
                    "chunk_index": chunk_index,
                    "start_char": start,
                    "end_char": end,
                    "metadata": metadata or {},
                }
            )
            chunk_index += 1
            start = end - self.chunk_overlap
        return chunks

    def chunk_documents(self, documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
        all_chunks = []
        for doc in documents:
            chunks = self.chunk_text(
                doc["content"],
                metadata={
                    **doc.get("metadata", {}),
                    "title": doc.get("title", ""),
                    "source": doc.get("source", ""),
                },
            )
            for chunk in chunks:
                chunk["title"] = doc.get("title", "")
                chunk["source"] = doc.get("source", "")
                chunk["source_url"] = doc.get("source_url", "")
            all_chunks.extend(chunks)
        logger.info("documents_chunked", input_docs=len(documents), output_chunks=len(all_chunks))
        return all_chunks
