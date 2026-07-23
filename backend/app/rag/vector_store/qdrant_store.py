from __future__ import annotations

import uuid
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointIdsList,
    PointStruct,
    VectorParams,
)

from app.core.config.settings import settings
from app.observability.logging import get_logger

logger = get_logger(__name__)


class QdrantVectorStore:
    def __init__(self) -> None:
        self.client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key or None,
        )
        self.collection = settings.qdrant_collection
        self.vector_size = settings.openai_embedding_dims

    async def ensure_collection(self) -> None:
        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]
        if self.collection not in collection_names:
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE),
            )
            logger.info("qdrant_collection_created", collection=self.collection)

    async def upsert_points(self, points: list[dict[str, Any]]) -> list[str]:
        ids = [str(uuid.uuid4()) for _ in points]
        qdrant_points = [
            PointStruct(
                id=ids[i],
                vector=points[i]["embedding"],
                payload={
                    "content": points[i]["content"],
                    "title": points[i].get("title", ""),
                    "source": points[i].get("source", ""),
                    "source_url": points[i].get("source_url", ""),
                    "chunk_index": points[i].get("chunk_index", 0),
                    "metadata": points[i].get("metadata", {}),
                },
            )
            for i in range(len(points))
        ]
        self.client.upsert(collection_name=self.collection, points=qdrant_points)
        logger.info("qdrant_upserted", count=len(qdrant_points))
        return ids

    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        score_threshold: float = 0.7,
        source_filter: str | None = None,
    ) -> list[dict[str, Any]]:
        query_filter = None
        if source_filter:
            query_filter = Filter(must=[FieldCondition(key="source", match=MatchValue(value=source_filter))])
        results = self.client.search(
            collection_name=self.collection,
            query_vector=query_embedding,
            limit=top_k,
            score_threshold=score_threshold,
            query_filter=query_filter,
        )
        return [
            {
                "id": str(hit.id),
                "score": hit.score,
                "content": hit.payload.get("content", ""),
                "title": hit.payload.get("title", ""),
                "source": hit.payload.get("source", ""),
                "source_url": hit.payload.get("source_url", ""),
                "metadata": hit.payload.get("metadata", {}),
            }
            for hit in results
        ]

    async def delete_points(self, point_ids: list[str]) -> None:
        self.client.delete(
            collection_name=self.collection,
            points_selector=PointIdsList(points=point_ids),
        )

    async def get_collection_info(self) -> dict[str, Any]:
        info = self.client.get_collection(self.collection)
        return {
            "name": info.name,
            "vectors_count": info.vectors_count,
            "points_count": info.points_count,
            "status": str(info.status),
        }
