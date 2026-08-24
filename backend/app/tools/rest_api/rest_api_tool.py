from __future__ import annotations

from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.security.encryption import mask_pii
from app.observability.logging import get_logger
from app.tools.base.tool_interface import BaseTool, ToolResult

logger = get_logger(__name__)


class RestAPITool(BaseTool):
    name = "rest_api"
    description = "Make generic REST API calls to external services"
    category = "integration"
    required_permissions = ["read:all_data"]
    risk_score = 0.3

    def __init__(self) -> None:
        super().__init__()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def _make_request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        async with httpx.AsyncClient() as client:
            return await client.request(method, url, timeout=self.timeout_seconds, **kwargs)

    async def execute(self, **kwargs: Any) -> ToolResult:
        method = kwargs.get("method", "GET").upper()
        url = kwargs.get("url", "")
        headers = kwargs.get("headers", {})
        data = kwargs.get("data")
        params = kwargs.get("params")
        if not url:
            return ToolResult(success=False, error="URL is required")
        try:
            response = await self._make_request(
                method, url, headers=headers, json=data, params=params
            )
            try:
                resp_data = response.json()
            except Exception:
                resp_data = {"text": response.text}
            return ToolResult(
                success=response.is_success,
                data=resp_data,
                metadata={"status_code": response.status_code, "url": mask_pii(url)},
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    async def validate_params(self, **kwargs: Any) -> bool:
        return "url" in kwargs

    async def health_check(self) -> bool:
        return True
