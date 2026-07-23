from __future__ import annotations

from enum import Enum
from functools import wraps
from typing import Any, Callable

from fastapi import HTTPException, status


class Permission(str, Enum):
    READ_OWN_DATA = "read:own_data"
    WRITE_OWN_DATA = "write:own_data"
    READ_ALL_DATA = "read:all_data"
    MANAGE_USERS = "manage:users"
    APPROVE_ACCESS = "approve:access"
    EXECUTE_TROUBLESHOOT = "execute:troubleshoot"
    MANAGE_WORKFLOWS = "manage:workflows"
    VIEW_AUDIT_LOGS = "view:audit_logs"
    MANAGE_POLICIES = "manage:policies"
    ADMIN_ACCESS = "admin:access"
    VIEW_DASHBOARD = "view:dashboard"
    MANAGE_KNOWLEDGE = "manage:knowledge"
    APPROVE_HIGH_RISK = "approve:high_risk"
    MANAGE_SYSTEM = "manage:system"


class Role(str, Enum):
    VIEWER = "viewer"
    USER = "user"
    OPERATOR = "operator"
    ENGINEER = "engineer"
    MANAGER = "manager"
    SECURITY_ADMIN = "security_admin"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


ROLE_PERMISSIONS: dict[Role, list[Permission]] = {
    Role.VIEWER: [Permission.READ_OWN_DATA, Permission.VIEW_DASHBOARD],
    Role.USER: [
        Permission.READ_OWN_DATA, Permission.WRITE_OWN_DATA,
        Permission.EXECUTE_TROUBLESHOOT, Permission.VIEW_DASHBOARD,
    ],
    Role.OPERATOR: [
        Permission.READ_OWN_DATA, Permission.WRITE_OWN_DATA,
        Permission.READ_ALL_DATA, Permission.EXECUTE_TROUBLESHOOT,
        Permission.VIEW_DASHBOARD, Permission.MANAGE_WORKFLOWS,
    ],
    Role.ENGINEER: [
        Permission.READ_OWN_DATA, Permission.WRITE_OWN_DATA,
        Permission.READ_ALL_DATA, Permission.EXECUTE_TROUBLESHOOT,
        Permission.VIEW_DASHBOARD, Permission.MANAGE_WORKFLOWS,
        Permission.MANAGE_KNOWLEDGE,
    ],
    Role.MANAGER: [
        Permission.READ_OWN_DATA, Permission.WRITE_OWN_DATA,
        Permission.READ_ALL_DATA, Permission.EXECUTE_TROUBLESHOOT,
        Permission.VIEW_DASHBOARD, Permission.MANAGE_WORKFLOWS,
        Permission.MANAGE_KNOWLEDGE, Permission.APPROVE_ACCESS,
    ],
    Role.SECURITY_ADMIN: [
        Permission.READ_OWN_DATA, Permission.WRITE_OWN_DATA,
        Permission.READ_ALL_DATA, Permission.EXECUTE_TROUBLESHOOT,
        Permission.VIEW_DASHBOARD, Permission.MANAGE_WORKFLOWS,
        Permission.MANAGE_KNOWLEDGE, Permission.APPROVE_ACCESS,
        Permission.VIEW_AUDIT_LOGS, Permission.MANAGE_POLICIES,
        Permission.APPROVE_HIGH_RISK,
    ],
    Role.ADMIN: [p for p in Permission],
    Role.SUPER_ADMIN: [p for p in Permission],
}


class RBACManager:
    @staticmethod
    def get_permissions_for_roles(roles: list[str]) -> list[str]:
        permissions: set[str] = set()
        for role_str in roles:
            try:
                role = Role(role_str)
                for perm in ROLE_PERMISSIONS.get(role, []):
                    permissions.add(perm.value)
            except ValueError:
                continue
        return sorted(permissions)

    @staticmethod
    def has_permission(user_permissions: list[str], required: Permission) -> bool:
        return required.value in user_permissions

    @staticmethod
    def check_permission(user_permissions: list[str], required: Permission) -> None:
        if not RBACManager.has_permission(user_permissions, required):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: requires '{required.value}'",
            )


def require_permission(permission: Permission) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            current_user = kwargs.get("current_user")
            if current_user is None:
                for arg in args:
                    if hasattr(arg, "permissions"):
                        current_user = arg
                        break
            if current_user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )
            user_perms = getattr(current_user, "permissions", [])
            RBACManager.check_permission(user_perms, permission)
            return await func(*args, **kwargs)
        return wrapper
    return decorator
