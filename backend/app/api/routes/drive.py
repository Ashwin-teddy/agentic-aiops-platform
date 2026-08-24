from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse

from app.api.dependencies.auth import CurrentUser, get_current_user
from app.core.config.settings import settings
from app.integrations.google_drive import drive_service
from app.observability.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/drive", tags=["Google Drive"])


@router.get("/auth-url")
async def get_auth_url(
    current_user: CurrentUser = Depends(get_current_user),
) -> dict:
    if not settings.google_oauth_client_id:
        raise HTTPException(status_code=503, detail="Google Drive integration is not configured")
    try:
        auth_url = await drive_service.build_auth_url(state=current_user.user_id)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    status = await drive_service.get_connection_status(current_user.user_id)
    return {"auth_url": auth_url, "connected": status["connected"], "email": status["email"]}


@router.get("/oauth-callback")
async def oauth_callback(code: str, state: str) -> RedirectResponse:
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing OAuth code or state")
    try:
        token_data = await drive_service.exchange_code(code)
        await drive_service.store_tokens(state, token_data)
    except Exception as e:
        logger.error("google_drive_oauth_callback_failed", error=str(e))
        raise HTTPException(status_code=502, detail=f"Google authorization failed: {e}")
    frontend_url = settings.cors_origins[0] if settings.cors_origins else ""
    redirect = (
        f"{frontend_url}/access?drive=connected" if frontend_url else "/access?drive=connected"
    )
    return RedirectResponse(url=redirect)


@router.get("/status")
async def get_status(
    current_user: CurrentUser = Depends(get_current_user),
) -> dict:
    return await drive_service.get_connection_status(current_user.user_id)


@router.post("/disconnect")
async def disconnect(
    current_user: CurrentUser = Depends(get_current_user),
) -> dict:
    await drive_service.disconnect(current_user.user_id)
    return {"connected": False}
