from __future__ import annotations

from typing import Any

from app.observability.logging import get_logger
from app.tools.base.tool_registry import get_tool_registry

logger = get_logger(__name__)


class NotificationAgent:
    name = "notification_agent"

    def __init__(self) -> None:
        self.tool_registry = get_tool_registry()

    async def notify_user(
        self,
        user_id: str,
        message: str,
        channels: list[str] | None = None,
        title: str = "",
        severity: str = "info",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        channels = channels or ["slack"]
        results: dict[str, Any] = {}
        for channel in channels:
            if channel == "slack":
                results["slack"] = await self._send_slack(user_id, message, title, severity)
            elif channel == "teams":
                results["teams"] = await self._send_teams(user_id, message, title)
            elif channel == "email":
                results["email"] = await self._send_email(user_id, message, title)
        logger.info("notification_sent", user_id=user_id, channels=channels, severity=severity)
        return {"success": True, "results": results}

    async def notify_approval_needed(
        self,
        approver_ids: list[str],
        request_id: str,
        resource_type: str,
        requester: str,
        risk_level: str,
    ) -> dict[str, Any]:
        message = (
            f"Access approval needed for {requester}\n"
            f"Resource: {resource_type}\n"
            f"Risk Level: {risk_level}\n"
            f"Please review in the dashboard."
        )
        results = {}
        slack = self.tool_registry.get("slack")
        if slack:
            result = await slack.safe_execute(
                action="send_message", channel="#access-approvals", text=message
            )
            results["slack"] = result.success
        email_tool = self.tool_registry.get("email")
        if email_tool:
            for approver_id in approver_ids:
                result = await email_tool.safe_execute(
                    action="send_email",
                    to=[approver_id],
                    subject=f"Action Required: Access Approval - {resource_type}",
                    body=message,
                )
                results[f"email_{approver_id}"] = result.success
        return results

    async def notify_incident(
        self,
        message: str,
        severity: str,
        affected_services: list[str] | None = None,
    ) -> dict[str, Any]:
        severity_channel = {
            "P1": "#incident-critical",
            "P2": "#incident-high",
            "P3": "#incident-medium",
            "P4": "#incident-low",
        }
        channel = severity_channel.get(severity, "#incidents")
        slack = self.tool_registry.get("slack")
        result: dict[str, Any] = {}
        if slack:
            sr = await slack.safe_execute(action="send_message", channel=channel, text=message)
            result["slack"] = sr.success
        return result

    async def _send_slack(self, user_id: str, message: str, title: str, severity: str) -> bool:
        slack = self.tool_registry.get("slack")
        if not slack:
            return False
        result = await slack.safe_execute(
            action="send_dm", user_id=user_id, text=f"*{title}*\n{message}" if title else message
        )
        return result.success

    async def _send_teams(self, user_id: str, message: str, title: str) -> bool:
        return self.tool_registry.get("microsoft_teams")

    async def _send_email(self, user_id: str, message: str, title: str) -> bool:
        email = self.tool_registry.get("email")
        if not email:
            return False
        result = await email.safe_execute(
            action="send_email", to=[user_id], subject=title or "AIOPS Notification", body=message
        )
        return result.success
