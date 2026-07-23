from __future__ import annotations

import json
from typing import Any

import redis.asyncio as redis

from app.core.config.settings import settings
from app.observability.logging import get_logger

logger = get_logger(__name__)


class OrganizationalMemory:
    def __init__(self) -> None:
        self.redis = redis.from_url(settings.redis_url, password=settings.redis_password or None, decode_responses=True)

    async def store_team_knowledge(self, team: str, key: str, value: Any) -> None:
        k = f"org:team:{team}:{key}"
        await self.redis.set(k, json.dumps(value), ex=604800)

    async def get_team_knowledge(self, team: str, key: str) -> Any | None:
        raw = await self.redis.get(f"org:team:{team}:{key}")
        return json.loads(raw) if raw else None

    async def store_policy(self, policy_name: str, policy_data: dict[str, Any]) -> None:
        await self.redis.set(f"org:policy:{policy_name}", json.dumps(policy_data), ex=604800)

    async def get_policy(self, policy_name: str) -> dict[str, Any] | None:
        raw = await self.redis.get(f"org:policy:{policy_name}")
        return json.loads(raw) if raw else None

    async def list_policies(self) -> list[str]:
        keys = await self.redis.keys("org:policy:*")
        return [k.replace("org:policy:", "") for k in keys]

    async def store_runbook_ref(self, service: str, runbook_id: str, summary: str) -> None:
        key = f"org:runbooks:{service}"
        entry = json.dumps({"runbook_id": runbook_id, "summary": summary})
        await self.redis.rpush(key, entry)

    async def get_runbook_refs(self, service: str) -> list[dict[str, Any]]:
        raw = await self.redis.lrange(f"org:runbooks:{service}", 0, -1)
        return [json.loads(item) for item in raw]

    async def store_incident_pattern(self, pattern_key: str, pattern_data: dict[str, Any]) -> None:
        await self.redis.set(f"org:incident_pattern:{pattern_key}", json.dumps(pattern_data), ex=604800)

    async def get_incident_pattern(self, pattern_key: str) -> dict[str, Any] | None:
        raw = await self.redis.get(f"org:incident_pattern:{pattern_key}")
        return json.loads(raw) if raw else None
