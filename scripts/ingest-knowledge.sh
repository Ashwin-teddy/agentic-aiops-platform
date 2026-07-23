#!/usr/bin/env bash
set -euo pipefail

echo "Ingesting documents into knowledge base..."
python -c "
import asyncio
from backend.app.rag.chunking.document_chunker import DocumentChunker
from backend.app.rag.embeddings.embedding_service import EmbeddingService
from backend.app.rag.vector_store.qdrant_store import QdrantVectorStore

async def ingest():
    chunker = DocumentChunker()
    embedder = EmbeddingService()
    store = QdrantVectorStore()
    await store.ensure_collection()
    print('Ready for document ingestion. Add documents to data/ directory.')

asyncio.run(ingest())
"
