from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from app.observability.logging import get_logger

logger = get_logger(__name__)


class AuditAgent:
    name = "audit_agent"

    def __init__(self) -> None:
        self.audit_logs: list[dict[str, Any]] = []

    async def log_action(
        self,
        user_id: str,
        session_id: str,
        action: str,
        resource_type: str = "",
        resource_id: str = "",
        details: dict[str, Any] | None = None,
        risk_score: float = 0.0,
        success: bool = True,
        error_message: str | None = None,
        ip_address: str = "",
        user_agent: str = "",
    ) -> dict[str, Any]:
        log_entry = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "session_id": session_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": details or {},
            "risk_score": risk_score,
            "success": success,
            "error_message": error_message,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.audit_logs.append(log_entry)
        logger.info(
            "audit_log_entry",
            audit_id=log_entry["id"],
            action=action,
            user=user_id,
            success=success,
        )
        return log_entry

    async def log_agent_execution(
        self,
        session_id: str,
        agent_name: str,
        action: str,
        input_summary: str,
        output_summary: str,
        duration_ms: float,
        success: bool,
        user_id: str = "",
    ) -> dict[str, Any]:
        return await self.log_action(
            user_id=user_id,
            session_id=session_id,
            action=f"agent.{agent_name}.{action}",
            details={
                "agent": agent_name,
                "input_summary": input_summary[:500],
                "output_summary": output_summary[:500],
                "duration_ms": duration_ms,
            },
            success=success,
        )

    async def log_security_event(
        self,
        user_id: str,
        event_type: str,
        details: dict[str, Any],
        ip_address: str = "",
    ) -> dict[str, Any]:
        return await self.log_action(
            user_id=user_id,
            action=f"security.{event_type}",
            resource_type="security",
            details=details,
            risk_score=0.8,
            ip_address=ip_address,
        )

    async def get_audit_trail(
        self,
        user_id: str | None = None,
        session_id: str | None = None,
        action: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        filtered = self.audit_logs
        if user_id:
            filtered = [l for l in filtered if l["user_id"] == user_id]
        if session_id:
            filtered = [l for l in filtered if l["session_id"] == session_id]
        if action:
            filtered = [l for l in filtered if l["action"] == action]
        return filtered[-limit:]
