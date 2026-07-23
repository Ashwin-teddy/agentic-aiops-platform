from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import redis.asyncio as redis

from app.core.config.settings import settings
from app.observability.logging import get_logger

logger = get_logger(__name__)


class ConversationMemory:
    def __init__(self) -> None:
        self.redis = redis.from_url(settings.redis_url, password=settings.redis_password or None, decode_responses=True)
        self.max_messages = 50
        self.ttl_seconds = 86400

    async def add_turn(self, user_id: str, session_id: str, user_message: str, assistant_message: str, intent: str = "") -> None:
        key = f"conversation:{user_id}"
        turn = {
            "session_id": session_id,
            "user_message": user_message,
            "assistant_message": assistant_message,
            "intent": intent,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await self.redis.rpush(key, json.dumps(turn))
        await self.redis.ltrim(key, -self.max_messages, -1)
        await self.redis.expire(key, self.ttl_seconds)

    async def get_history(self, user_id: str, limit: int = 20) -> list[dict[str, Any]]:
        key = f"conversation:{user_id}"
        messages = await self.redis.lrange(key, -limit, -1)
        return [json.loads(msg) for msg in messages]

    async def search_conversations(self, user_id: str, query: str) -> list[dict[str, Any]]:
        history = await self.get_history(user_id, limit=self.max_messages)
        query_lower = query.lower()
        return [msg for msg in history if query_lower in msg.get("user_message", "").lower() or query_lower in msg.get("assistant_message", "").lower()]

    async def clear_history(self, user_id: str) -> None:
        await self.redis.delete(f"conversation:{user_id}")

    async def get_stats(self, user_id: str) -> dict[str, Any]:
        key = f"conversation:{user_id}"
        total_turns = await self.redis.llen(key)
        return {"user_id": user_id, "total_turns": total_turns}
