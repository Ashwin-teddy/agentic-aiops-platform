from __future__ import annotations

from typing import Any

import httpx

from app.core.config.settings import settings
from app.tools.base.tool_interface import BaseTool, ToolResult


class SlackTool(BaseTool):
    name = "slack"
    description = "Send messages and manage Slack channels"
    category = "communication"
    required_permissions = ["read:own_data"]
    risk_score = 0.1

    def __init__(self) -> None:
        super().__init__()
        self.base_url = "https://slack.com/api"
        self.headers = {"Authorization": f"Bearer {settings.slack_bot_token}", "Content-Type": "application/json"}

    async def _post(self, method: str, **kwargs: Any) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{self.base_url}/{method}", headers=self.headers, timeout=self.timeout_seconds, **kwargs)
            resp.raise_for_status()
            data = resp.json()
            if not data.get("ok"):
                return {"error": data.get("error", "unknown_error")}
            return data

    async def execute(self, **kwargs: Any) -> ToolResult:
        action = kwargs.get("action", "send_message")
        if action == "send_message":
            data = await self._post("chat.postMessage", json={
                "channel": kwargs["channel"],
                "text": kwargs.get("text", ""),
                "blocks": kwargs.get("blocks"),
            })
            return ToolResult(success="error" not in data, data=data)
        elif action == "list_channels":
            data = await self._post("conversations.list", json={"types": "public_channel,private_channel", "limit": 100})
            return ToolResult(success="error" not in data, data=data.get("channels", []))
        elif action == "send_dm":
            data = await self._post("chat.postMessage", json={
                "channel": kwargs["user_id"],
                "text": kwargs.get("text", ""),
            })
            return ToolResult(success="error" not in data, data=data)
        return ToolResult(success=False, error=f"Unknown action: {action}")

    async def validate_params(self, **kwargs: Any) -> bool:
        return "action" in kwargs

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self.base_url}/auth.test", headers=self.headers, timeout=10)
                return resp.json().get("ok", False)
        except Exception:
            return False
