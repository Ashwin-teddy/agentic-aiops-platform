from __future__ import annotations

from typing import Any

import httpx

from app.core.config.settings import settings
from app.tools.base.tool_interface import BaseTool, ToolResult


class OktaTool(BaseTool):
    name = "okta"
    description = "Manage Okta users, groups, and applications"
    category = "identity"
    required_permissions = ["manage:users"]
    risk_score = 0.7

    def __init__(self) -> None:
        super().__init__()
        self.base_url = f"https://{settings.okta_domain}/api/v1"
        self.headers = {"Accept": "application/json", "Content-Type": "application/json"}

    async def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            resp = await client.request(
                method, f"{self.base_url}{path}",
                headers=self.headers,
                timeout=self.timeout_seconds,
                **kwargs,
            )
            resp.raise_for_status()
            return resp.json()

    async def execute(self, **kwargs: Any) -> ToolResult:
        action = kwargs.get("action", "get_user")
        if action == "get_user":
            user_id = kwargs["user_id"]
            data = await self._request("GET", f"/users/{user_id}")
            return ToolResult(success=True, data=data)
        elif action == "activate_user":
            user_id = kwargs["user_id"]
            data = await self._request("POST", f"/users/{user_id}/lifecycle/activate")
            return ToolResult(success=True, data=data)
        elif action == "assign_app":
            user_id = kwargs["user_id"]
            app_id = kwargs["app_id"]
            data = await self._request("POST", f"/apps/{app_id}/users", json={"id": user_id})
            return ToolResult(success=True, data=data)
        elif action == "list_groups":
            user_id = kwargs["user_id"]
            data = await self._request("GET", f"/users/{user_id}/groups")
            return ToolResult(success=True, data=data)
        return ToolResult(success=False, error=f"Unknown action: {action}")

    async def validate_params(self, **kwargs: Any) -> bool:
        return "action" in kwargs and "user_id" in kwargs

    async def health_check(self) -> bool:
        try:
            await self._request("GET", "/apps")
            return True
        except Exception:
            return False
