from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security.jwt import verify_token
from app.core.security.rbac import Permission, RBACManager
from app.observability.logging import get_logger

logger = get_logger(__name__)
security = HTTPBearer()


class CurrentUser:
    def __init__(
        self,
        user_id: str,
        email: str = "",
        display_name: str = "",
        roles: list[str] | None = None,
        permissions: list[str] | None = None,
        session_id: str = "",
    ) -> None:
        self.user_id = user_id
        self.email = email
        self.display_name = display_name
        self.roles = roles or []
        self.permissions = permissions or []
        self.session_id = session_id

    def has_permission(self, permission: Permission) -> bool:
        return RBACManager.has_permission(self.permissions, permission)

    def require_permission(self, permission: Permission) -> None:
        RBACManager.check_permission(self.permissions, permission)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> CurrentUser:
    try:
        payload = verify_token(credentials.credentials)
        return CurrentUser(
            user_id=payload.sub,
            email=payload.email,
            display_name=payload.display_name,
            roles=payload.roles,
            permissions=payload.permissions,
            session_id=payload.session_id,
        )
    except ValueError as e:
        logger.error("auth_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from e
