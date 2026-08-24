from __future__ import annotations

from typing import Any

import httpx

from app.core.config.settings import settings
from app.tools.base.tool_interface import BaseTool, ToolResult


class JiraTool(BaseTool):
    name = "jira"
    description = "Manage Jira issues, projects, and workflows"
    category = "project_management"
    required_permissions = ["read:all_data"]
    risk_score = 0.2

    def __init__(self) -> None:
        super().__init__()
        self.base_url = f"{settings.jira_url}/rest/api/3"
        self.auth = (settings.jira_username, settings.jira_api_token)
        self.headers = {"Content-Type": "application/json", "Accept": "application/json"}

    async def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            resp = await client.request(
                method,
                f"{self.base_url}{path}",
                auth=self.auth,
                headers=self.headers,
                timeout=self.timeout_seconds,
                **kwargs,
            )
            resp.raise_for_status()
            return resp.json()

    async def execute(self, **kwargs: Any) -> ToolResult:
        action = kwargs.get("action", "get_issue")
        if action == "get_issue":
            issue_key = kwargs["issue_key"]
            data = await self._request("GET", f"/issue/{issue_key}")
            return ToolResult(success=True, data=data)
        if action == "create_issue":
            data = await self._request(
                "POST",
                "/issue",
                json={
                    "fields": {
                        "project": {"key": kwargs.get("project_key", "OPS")},
                        "summary": kwargs.get("summary", ""),
                        "description": kwargs.get("description", ""),
                        "issuetype": {"name": kwargs.get("issue_type", "Task")},
                    }
                },
            )
            return ToolResult(success=True, data=data)
        if action == "search":
            jql = kwargs.get("jql", "")
            data = await self._request("GET", "/search", params={"jql": jql, "maxResults": 10})
            return ToolResult(success=True, data=data.get("issues", []))
        if action == "add_comment":
            issue_key = kwargs["issue_key"]
            comment = kwargs["comment"]
            data = await self._request(
                "POST", f"/issue/{issue_key}/comment", json={"body": comment}
            )
            return ToolResult(success=True, data=data)
        if action == "assign_issue":
            issue_key = kwargs["issue_key"]
            assignee = kwargs.get("assignee", "")
            await self._request("PUT", f"/issue/{issue_key}/assignee", json={"accountId": assignee})
            return ToolResult(success=True, data={"message": f"Issue {issue_key} assigned"})
        return ToolResult(success=False, error=f"Unknown action: {action}")

    async def validate_params(self, **kwargs: Any) -> bool:
        return "action" in kwargs

    async def health_check(self) -> bool:
        try:
            await self._request("GET", "/myself")
            return True
        except Exception:
            return False
