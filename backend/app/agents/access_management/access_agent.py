from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from app.domain.enums.risk import RiskLevel
from app.domain.enums.status import TaskStatus
from app.observability.logging import get_logger
from app.tools.base.tool_registry import get_tool_registry

logger = get_logger(__name__)

RESOURCE_TOOL_MAP: dict[str, str] = {
    "jira": "jira",
    "confluence": "rest_api",
    "github": "github",
    "aws_iam": "aws_iam",
    "kubernetes": "kubernetes",
    "azure_ad": "azure_ad",
    "okta": "okta",
    "servicenow": "servicenow",
}


class AccessManagementAgent:
    name = "access_management_agent"

    def __init__(self) -> None:
        self.tool_registry = get_tool_registry()

    async def process_access_request(
        self,
        user_id: str,
        resource_type: str,
        resource_identifier: str,
        access_type: str,
        risk_level: RiskLevel,
        justification: str = "",
        auto_execute: bool = False,
    ) -> dict[str, Any]:
        request_id = str(uuid.uuid4())
        result: dict[str, Any] = {
            "request_id": request_id,
            "user_id": user_id,
            "resource_type": resource_type,
            "resource_identifier": resource_identifier,
            "access_type": access_type,
            "risk_level": risk_level.value,
            "status": "pending",
            "created_at": datetime.now(UTC).isoformat(),
        }
        if risk_level == RiskLevel.LOW and auto_execute:
            execution_result = await self._execute_access_grant(
                resource_type, resource_identifier, access_type, user_id
            )
            result["execution_result"] = execution_result
            result["status"] = (
                TaskStatus.COMPLETED.value
                if execution_result.get("success")
                else TaskStatus.FAILED.value
            )
        else:
            result["status"] = TaskStatus.WAITING_APPROVAL.value
            result["message"] = "Access request requires approval"
        logger.info(
            "access_request_processed",
            request_id=request_id,
            resource=resource_type,
            risk=risk_level.value,
            status=result["status"],
        )
        return result

    async def _execute_access_grant(
        self,
        resource_type: str,
        resource_identifier: str,
        access_type: str,
        user_id: str,
    ) -> dict[str, Any]:
        tool_name = RESOURCE_TOOL_MAP.get(resource_type)
        if not tool_name:
            return {
                "success": False,
                "error": f"No tool available for resource type: {resource_type}",
            }
        tool = self.tool_registry.get(tool_name)
        if not tool:
            return {"success": False, "error": f"Tool '{tool_name}' not registered"}
        params = self._build_tool_params(resource_type, resource_identifier, access_type, user_id)
        result = await tool.safe_execute(**params)
        return {"success": result.success, "data": result.data, "error": result.error}

    def _build_tool_params(
        self, resource_type: str, resource_identifier: str, access_type: str, user_id: str
    ) -> dict[str, Any]:
        if resource_type == "github":
            return {"action": "list_prs", "repo": resource_identifier}
        if resource_type == "jira":
            return {"action": "get_issue", "issue_key": resource_identifier}
        if resource_type == "azure_ad":
            if access_type == "read":
                return {"action": "get_user", "user_id": user_id}
            return {"action": "add_to_group", "user_id": user_id, "group_id": resource_identifier}
        if resource_type == "aws_iam":
            if access_type == "read":
                return {"action": "list_users"}
            return {
                "action": "attach_policy",
                "username": user_id,
                "policy_arn": resource_identifier,
            }
        if resource_type == "kubernetes":
            return {"action": "list_pods", "namespace": resource_identifier}
        return {"action": "get_user", "user_id": user_id}

    async def revoke_access(
        self, resource_type: str, resource_identifier: str, user_id: str
    ) -> dict[str, Any]:
        tool_name = RESOURCE_TOOL_MAP.get(resource_type)
        if not tool_name:
            return {"success": False, "error": f"No tool for resource: {resource_type}"}
        logger.info("access_revoked", resource=resource_type, user=user_id)
        return {
            "success": True,
            "message": f"Access revoked for user {user_id} on {resource_type}/{resource_identifier}",
        }
