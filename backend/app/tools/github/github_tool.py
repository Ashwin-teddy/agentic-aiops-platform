from __future__ import annotations

from typing import Any

import httpx

from app.core.config.settings import settings
from app.tools.base.tool_interface import BaseTool, ToolResult


class GitHubTool(BaseTool):
    name = "github"
    description = "Interact with GitHub repos, PRs, issues, and actions"
    category = "scm"
    required_permissions = ["read:all_data"]
    risk_score = 0.4

    def __init__(self) -> None:
        super().__init__()
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"Bearer {settings.github_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            resp = await client.request(
                method, f"{self.base_url}{path}",
                headers=self.headers, timeout=self.timeout_seconds, **kwargs,
            )
            resp.raise_for_status()
            if resp.status_code == 204:
                return {}
            return resp.json()

    async def execute(self, **kwargs: Any) -> ToolResult:
        action = kwargs.get("action", "get_repo")
        org = kwargs.get("org", settings.github_org)
        if action == "get_repo":
            repo = kwargs["repo"]
            data = await self._request("GET", f"/repos/{org}/{repo}")
            return ToolResult(success=True, data=data)
        elif action == "list_prs":
            repo = kwargs["repo"]
            state = kwargs.get("state", "open")
            data = await self._request("GET", f"/repos/{org}/{repo}/pulls", params={"state": state, "per_page": 10})
            return ToolResult(success=True, data=data)
        elif action == "get_pr":
            repo = kwargs["repo"]
            pr_number = kwargs["pr_number"]
            data = await self._request("GET", f"/repos/{org}/{repo}/pulls/{pr_number}")
            return ToolResult(success=True, data=data)
        elif action == "list_issues":
            repo = kwargs["repo"]
            data = await self._request("GET", f"/repos/{org}/{repo}/issues", params={"per_page": 10})
            return ToolResult(success=True, data=data)
        elif action == "search_code":
            query = kwargs.get("query", "")
            data = await self._request("GET", "/search/code", params={"q": f"{query} org:{org}"})
            return ToolResult(success=True, data=data.get("items", []))
        elif action == "get_workflow_runs":
            repo = kwargs["repo"]
            data = await self._request("GET", f"/repos/{org}/{repo}/actions/runs", params={"per_page": 10})
            return ToolResult(success=True, data=data.get("workflow_runs", []))
        return ToolResult(success=False, error=f"Unknown action: {action}")

    async def validate_params(self, **kwargs: Any) -> bool:
        return "action" in kwargs

    async def health_check(self) -> bool:
        try:
            await self._request("GET", "/user")
            return True
        except Exception:
            return False
