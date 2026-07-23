from __future__ import annotations

from typing import Any

import boto3
from botocore.exceptions import ClientError

from app.core.config.settings import settings
from app.tools.base.tool_interface import BaseTool, ToolResult


class AWSIAMTool(BaseTool):
    name = "aws_iam"
    description = "Manage AWS IAM users, roles, and policies"
    category = "cloud"
    required_permissions = ["admin:access"]
    risk_score = 0.9

    def __init__(self) -> None:
        super().__init__()

    def _get_client(self, service: str = "iam") -> Any:
        return boto3.client(
            service,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region,
        )

    async def execute(self, **kwargs: Any) -> ToolResult:
        action = kwargs.get("action", "list_users")
        try:
            if action == "list_users":
                client = self._get_client()
                data = client.list_users()
                users = [{"UserName": u["UserName"], "Arn": u["Arn"], "CreateDate": str(u["CreateDate"])} for u in data.get("Users", [])]
                return ToolResult(success=True, data={"users": users})
            elif action == "get_user":
                client = self._get_client()
                username = kwargs["username"]
                data = client.get_user(UserName=username)
                return ToolResult(success=True, data=data.get("User", {}))
            elif action == "list_roles":
                client = self._get_client()
                data = client.list_roles()
                roles = [{"RoleName": r["RoleName"], "Arn": r["Arn"]} for r in data.get("Roles", [])]
                return ToolResult(success=True, data={"roles": roles})
            elif action == "attach_policy":
                client = self._get_client()
                client.attach_user_policy(
                    UserName=kwargs["username"],
                    PolicyArn=kwargs["policy_arn"],
                )
                return ToolResult(success=True, data={"message": f"Policy attached to {kwargs['username']}"})
            elif action == "create_access_key":
                client = self._get_client()
                data = client.create_access_key(UserName=kwargs["username"])
                ak = data["AccessKey"]
                return ToolResult(success=True, data={"AccessKeyId": ak["AccessKeyId"], "SecretAccessKey": ak["SecretAccessKey"]})
            elif action == "list_policies":
                client = self._get_client()
                data = client.list_policies(Scope="Local")
                return ToolResult(success=True, data={"policies": data.get("Policies", [])})
        except ClientError as e:
            return ToolResult(success=False, error=str(e))
        return ToolResult(success=False, error=f"Unknown action: {action}")

    async def validate_params(self, **kwargs: Any) -> bool:
        return "action" in kwargs

    async def health_check(self) -> bool:
        try:
            client = self._get_client()
            client.list_users(MaxItems=1)
            return True
        except Exception:
            return False
