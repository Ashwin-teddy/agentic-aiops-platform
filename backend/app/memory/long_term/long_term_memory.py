from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

import redis.asyncio as redis

from app.core.config.settings import settings
from app.observability.logging import get_logger

logger = get_logger(__name__)


class LongTermMemory:
    def __init__(self) -> None:
        self.redis = redis.from_url(
            settings.redis_url, password=settings.redis_password or None, decode_responses=True
        )

    async def store_preference(self, user_id: str, key: str, value: Any) -> None:
        pref_key = f"user_prefs:{user_id}"
        await self.redis.hset(pref_key, key, json.dumps(value))
        await self.redis.expire(pref_key, 2592000)

    async def get_preference(self, user_id: str, key: str) -> Any | None:
        raw = await self.redis.hget(f"user_prefs:{user_id}", key)
        return json.loads(raw) if raw else None

    async def get_all_preferences(self, user_id: str) -> dict[str, Any]:
        raw = await self.redis.hgetall(f"user_prefs:{user_id}")
        return {k: json.loads(v) for k, v in raw.items()}

    async def store_interaction_pattern(
        self, user_id: str, pattern_type: str, pattern_data: dict[str, Any]
    ) -> None:
        key = f"user_patterns:{user_id}:{pattern_type}"
        await self.redis.set(key, json.dumps(pattern_data), ex=2592000)

    async def get_interaction_pattern(
        self, user_id: str, pattern_type: str
    ) -> dict[str, Any] | None:
        raw = await self.redis.get(f"user_patterns:{user_id}:{pattern_type}")
        return json.loads(raw) if raw else None

    async def store_resolved_incident(
        self, user_id: str, incident_id: str, resolution: dict[str, Any]
    ) -> None:
        key = f"resolved:{user_id}"
        entry = {
            "incident_id": incident_id,
            "resolution": resolution,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        await self.redis.rpush(key, json.dumps(entry))
        await self.redis.ltrim(key, -100, -1)

    async def get_resolved_incidents(self, user_id: str, limit: int = 10) -> list[dict[str, Any]]:
        raw = await self.redis.lrange(f"resolved:{user_id}", -limit, -1)
        return [json.loads(item) for item in raw]
