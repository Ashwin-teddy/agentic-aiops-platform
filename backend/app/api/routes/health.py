from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies.auth import CurrentUser, get_current_user

router = APIRouter(tags=["Health & Monitoring"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy", "version": "1.0.0"}


@router.get("/metrics")
async def metrics() -> dict:
    return {"status": "metrics available"}


@router.get("/tools")
async def list_tools(current_user: CurrentUser = Depends(get_current_user)) -> list[dict]:
    from app.tools.base.tool_registry import get_tool_registry

    registry = get_tool_registry()
    return registry.list_tools()


@router.get("/tools/health")
async def tool_health_check(current_user: CurrentUser = Depends(get_current_user)) -> dict:
    from app.tools.base.tool_registry import get_tool_registry

    registry = get_tool_registry()
    return await registry.health_check_all()
