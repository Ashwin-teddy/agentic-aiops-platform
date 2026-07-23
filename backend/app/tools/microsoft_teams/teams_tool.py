from __future__ import annotations

from typing import Any

import httpx

from app.core.config.settings import settings
from app.tools.base.tool_interface import BaseTool, ToolResult


class MicrosoftTeamsTool(BaseTool):
    name = "microsoft_teams"
    description = "Send messages and manage Microsoft Teams channels"
    category = "communication"
    required_permissions = ["read:own_data"]
    risk_score = 0.1

    def __init__(self) -> None:
        super().__init__()
        self.base_url = "https://graph.microsoft.com/v1.0"
        self._token: str | None = None

    async def _get_token(self) -> str:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"https://login.microsoftonline.com/{settings.teams_tenant_id}/oauth2/v2.0/token",
                data={
                    "client_id": settings.teams_client_id,
                    "client_secret": settings.teams_client_secret,
                    "scope": "https://graph.microsoft.com/.default",
                    "grant_type": "client_credentials",
                },
            )
            resp.raise_for_status()
            return resp.json()["access_token"]

    async def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        if not self._token:
            self._token = await self._get_token()
        async with httpx.AsyncClient() as client:
            resp = await client.request(
                method, f"{self.base_url}{path}",
                headers={"Authorization": f"Bearer {self._token}"},
                timeout=self.timeout_seconds, **kwargs,
            )
            resp.raise_for_status()
            return resp.json() if resp.content else {}

    async def execute(self, **kwargs: Any) -> ToolResult:
        action = kwargs.get("action", "send_message")
        if action == "send_message":
            team_id = kwargs["team_id"]
            channel_id = kwargs["channel_id"]
            data = await self._request("POST", f"/teams/{team_id}/channels/{channel_id}/messages", json={
                "body": {"content": kwargs.get("text", "")},
            })
            return ToolResult(success=True, data=data)
        elif action == "list_teams":
            data = await self._request("GET", "/me/joinedTeams")
            return ToolResult(success=True, data=data.get("value", []))
        elif action == "list_channels":
            team_id = kwargs["team_id"]
            data = await self._request("GET", f"/teams/{team_id}/channels")
            return ToolResult(success=True, data=data.get("value", []))
        return ToolResult(success=False, error=f"Unknown action: {action}")

    async def validate_params(self, **kwargs: Any) -> bool:
        return "action" in kwargs

    async def health_check(self) -> bool:
        try:
            await self._get_token()
            return True
        except Exception:
            return False
