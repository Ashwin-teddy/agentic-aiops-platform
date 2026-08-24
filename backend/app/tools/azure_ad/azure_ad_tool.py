from __future__ import annotations

from typing import Any

import httpx

from app.core.config.settings import settings
from app.tools.base.tool_interface import BaseTool, ToolResult


class AzureADTool(BaseTool):
    name = "azure_ad"
    description = "Manage Azure AD users, groups, and role assignments"
    category = "identity"
    required_permissions = ["manage:users"]
    risk_score = 0.8

    def __init__(self) -> None:
        super().__init__()
        self.base_url = "https://graph.microsoft.com/v1.0"
        self.client_id = settings.azure_ad_client_id
        self.client_secret = settings.azure_ad_client_secret
        self.tenant_id = settings.azure_ad_tenant_id
        self._token: str | None = None

    async def _get_token(self) -> str:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token",
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
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
                method,
                f"{self.base_url}{path}",
                headers={"Authorization": f"Bearer {self._token}"},
                timeout=self.timeout_seconds,
                **kwargs,
            )
            if resp.status_code == 401:
                self._token = await self._get_token()
                resp = await client.request(
                    method,
                    f"{self.base_url}{path}",
                    headers={"Authorization": f"Bearer {self._token}"},
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
        if action == "list_groups":
            user_id = kwargs["user_id"]
            data = await self._request("GET", f"/users/{user_id}/memberOf")
            return ToolResult(success=True, data=data)
        if action == "add_to_group":
            user_id = kwargs["user_id"]
            group_id = kwargs["group_id"]
            await self._request(
                "POST",
                f"/groups/{group_id}/members",
                json={"@odata.id": f"{self.base_url}/users/{user_id}"},
            )
            return ToolResult(
                success=True, data={"message": f"User {user_id} added to group {group_id}"}
            )
        if action == "assign_role":
            user_id = kwargs["user_id"]
            role_id = kwargs["role_id"]
            await self._request(
                "POST",
                "/roleManagement/directory/roleAssignments",
                json={
                    "principalId": user_id,
                    "roleDefinitionId": role_id,
                    "directoryScopeId": "/",
                },
            )
            return ToolResult(
                success=True, data={"message": f"Role {role_id} assigned to user {user_id}"}
            )
        return ToolResult(success=False, error=f"Unknown action: {action}")

    async def validate_params(self, **kwargs: Any) -> bool:
        action = kwargs.get("action", "get_user")
        if action in ("get_user", "list_groups", "add_to_group", "assign_role"):
            return "user_id" in kwargs
        return False

    async def health_check(self) -> bool:
        try:
            await self._get_token()
            return True
        except Exception:
            return False
