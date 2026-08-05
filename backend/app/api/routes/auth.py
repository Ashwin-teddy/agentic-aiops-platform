from __future__ import annotations

import hashlib
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select

from app.api.dependencies.auth import CurrentUser, get_current_user
from app.api.schemas.auth import LoginRequest, RegisterRequest, AzureADLoginRequest, TokenResponse, UserResponse
from app.core.security.jwt import create_token_pair
from app.core.security.oauth2 import AzureADProvider
from app.db.session import get_session
from app.db.models.user import UserModel
from app.observability.logging import get_logger

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = get_logger(__name__)

azure_ad_provider = AzureADProvider()


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest) -> TokenResponse:
    logger.info("login_attempt", email=request.email)
    async with get_session() as session:
        result = await session.execute(select(UserModel).where(UserModel.email == request.email))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
        password_hash = hashlib.sha256(request.password.encode()).hexdigest()
        if user.password_hash != password_hash:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
        tokens = create_token_pair(
            subject=str(user.id),
            roles=[user.role],
            permissions=["read:own_data", "view:dashboard", "manage:access", "manage:approvals"],
            extra_claims={"email": user.email, "display_name": user.display_name},
        )
        return TokenResponse(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            expires_in=tokens.expires_in,
        )


@router.post("/register", response_model=TokenResponse)
async def register(request: RegisterRequest) -> TokenResponse:
    logger.info("register_attempt", email=request.email)
    async with get_session() as session:
        existing = await session.execute(select(UserModel).where(UserModel.email == request.email))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
        user = UserModel(
            id=uuid.uuid4(),
            email=request.email,
            display_name=request.display_name,
            password_hash=hashlib.sha256(request.password.encode()).hexdigest(),
            role="user",
        )
        session.add(user)
        await session.flush()
        tokens = create_token_pair(
            subject=str(user.id),
            roles=[user.role],
            permissions=["read:own_data", "view:dashboard", "manage:access", "manage:approvals"],
            extra_claims={"email": user.email, "display_name": user.display_name},
        )
        return TokenResponse(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            expires_in=tokens.expires_in,
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
        display_name=current_user.display_name,
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
