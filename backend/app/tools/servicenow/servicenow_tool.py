from __future__ import annotations

from typing import Any

import httpx

from app.core.config.settings import settings
from app.tools.base.tool_interface import BaseTool, ToolResult


class ServiceNowTool(BaseTool):
    name = "servicenow"
    description = "Interact with ServiceNow for incidents, changes, and knowledge base"
    category = "itsm"
    required_permissions = ["read:all_data"]
    risk_score = 0.3

    def __init__(self) -> None:
        super().__init__()
        self.base_url = settings.servicenow_url.rstrip("/") + "/api/now"
        self.auth = (settings.servicenow_username, settings.servicenow_password)
        self.headers = {"Content-Type": "application/json", "Accept": "application/json"}

    async def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            resp = await client.request(
                method, f"{self.base_url}{path}",
                auth=self.auth, headers=self.headers,
                timeout=self.timeout_seconds, **kwargs,
            )
            resp.raise_for_status()
            return resp.json()

    async def execute(self, **kwargs: Any) -> ToolResult:
        action = kwargs.get("action", "get_incident")
        if action == "get_incident":
            sys_id = kwargs["sys_id"]
            data = await self._request("GET", f"/table/incident/{sys_id}")
            return ToolResult(success=True, data=data.get("result", {}))
        elif action == "create_incident":
            data = await self._request("POST", "/table/incident", json={
                "short_description": kwargs.get("short_description", ""),
                "description": kwargs.get("description", ""),
                "urgency": kwargs.get("urgency", "3"),
                "impact": kwargs.get("impact", "3"),
                "assignment_group": kwargs.get("assignment_group", ""),
            })
            return ToolResult(success=True, data=data.get("result", {}))
        elif action == "search_knowledge":
            query = kwargs.get("query", "")
            data = await self._request("GET", f"/table/knowledge_base?sysparm_query=textLIKE{query}&sysparm_limit=10")
            return ToolResult(success=True, data=data.get("result", []))
        elif action == "get_cmdb":
            sys_id = kwargs.get("sys_id")
            data = await self._request("GET", f"/table/cmdb_ci/{sys_id}")
            return ToolResult(success=True, data=data.get("result", {}))
        return ToolResult(success=False, error=f"Unknown action: {action}")

    async def validate_params(self, **kwargs: Any) -> bool:
        return "action" in kwargs

    async def health_check(self) -> bool:
        try:
            await self._request("GET", "/table/incident?sysparm_limit=1")
            return True
        except Exception:
            return False
