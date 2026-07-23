from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.dependencies.auth import CurrentUser, get_current_user
from app.api.schemas.auth import LoginRequest, AzureADLoginRequest, TokenResponse, UserResponse
from app.core.security.jwt import create_token_pair
from app.core.security.oauth2 import AzureADProvider
from app.observability.logging import get_logger

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = get_logger(__name__)

azure_ad_provider = AzureADProvider()


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest) -> TokenResponse:
    from app.core.security.encryption import hash_secret
    logger.info("login_attempt", email=request.email)
    return TokenResponse(
        access_token="access_token_placeholder",
        refresh_token="refresh_token_placeholder",
        expires_in=1800,
    )


@router.get("/azure-ad/authorize")
async def azure_ad_authorize() -> dict[str, str]:
    import secrets
    state = secrets.token_urlsafe(32)
    url = await azure_ad_provider.get_authorization_url(state)
    return {"authorization_url": url, "state": state}


@router.post("/azure-ad/callback", response_model=TokenResponse)
async def azure_ad_callback(request: AzureADLoginRequest) -> TokenResponse:
    try:
        token_data = await azure_ad_provider.exchange_code(request.code)
        user_info = await azure_ad_provider.get_user_info(token_data["access_token"])
        tokens = create_token_pair(
            subject=user_info["id"],
            roles=["user"],
            permissions=["read:own_data", "view:dashboard"],
        )
        return TokenResponse(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            expires_in=tokens.expires_in,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser = Depends(get_current_user)) -> UserResponse:
    return UserResponse(
        id=current_user.user_id,
        email=current_user.email,
        display_name=current_user.email,
        role=current_user.roles[0] if current_user.roles else "user",
        permissions=current_user.permissions,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str) -> TokenResponse:
    from app.core.security.jwt import verify_token
    try:
        payload = verify_token(refresh_token, expected_type="refresh")
        tokens = create_token_pair(subject=payload.sub)
        return TokenResponse(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            expires_in=tokens.expires_in,
        )
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
