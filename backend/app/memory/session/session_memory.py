from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

import redis.asyncio as redis

from app.core.config.settings import settings
from app.observability.logging import get_logger

logger = get_logger(__name__)


class SessionMemory:
    def __init__(self) -> None:
        self.redis = redis.from_url(settings.redis_url, password=settings.redis_password or None, decode_responses=True)
        self.ttl_seconds = 3600

    async def create_session(self, user_id: str) -> str:
        session_id = str(uuid.uuid4())
        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "messages": json.dumps([]),
            "context": json.dumps({}),
            "status": "active",
        }
        await self.redis.hset(f"session:{session_id}", mapping=session_data)
        await self.redis.expire(f"session:{session_id}", self.ttl_seconds)
        return session_id

    async def get_session(self, session_id: str) -> dict[str, Any] | None:
        data = await self.redis.hgetall(f"session:{session_id}")
        if not data:
            return None
        data["messages"] = json.loads(data.get("messages", "[]"))
        data["context"] = json.loads(data.get("context", "{}"))
        return data

    async def add_message(self, session_id: str, role: str, content: str, metadata: dict[str, Any] | None = None) -> None:
        session = await self.get_session(session_id)
        if not session:
            return
        messages = session["messages"]
        messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata or {},
        })
        await self.redis.hset(f"session:{session_id}", "messages", json.dumps(messages))
        await self.redis.expire(f"session:{session_id}", self.ttl_seconds)

    async def update_context(self, session_id: str, key: str, value: Any) -> None:
        session = await self.get_session(session_id)
        if not session:
            return
        context = session["context"]
        context[key] = value
        await self.redis.hset(f"session:{session_id}", "context", json.dumps(context))
        await self.redis.expire(f"session:{session_id}", self.ttl_seconds)

    async def get_context(self, session_id: str) -> dict[str, Any]:
        session = await self.get_session(session_id)
        return session.get("context", {}) if session else {}

    async def close_session(self, session_id: str) -> None:
        await self.redis.hset(f"session:{session_id}", "status", "closed")

    async def delete_session(self, session_id: str) -> None:
        await self.redis.delete(f"session:{session_id}")
