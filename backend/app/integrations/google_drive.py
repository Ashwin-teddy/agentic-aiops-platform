from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode

import httpx
from sqlalchemy import select

from app.core.config.settings import settings
from app.core.security.encryption import decrypt_value, encrypt_value
from app.db.models.google_drive_token import GoogleDriveTokenModel
from app.db.session import get_session
from app.observability.logging import get_logger

logger = get_logger(__name__)

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
GOOGLE_DRIVE_PERMISSIONS_URL = "https://www.googleapis.com/drive/v3/files/{file_id}/permissions"

DRIVE_SCOPES = "https://www.googleapis.com/auth/drive https://www.googleapis.com/auth/userinfo.email"

ROLE_MAP = {
    "read": "reader",
    "write": "writer",
    "admin": "owner",
}

_ID_PATTERNS = [
    re.compile(r"/file/d/([a-zA-Z0-9_-]+)"),
    re.compile(r"/drive/folders/([a-zA-Z0-9_-]+)"),
    re.compile(r"/open\?id=([a-zA-Z0-9_-]+)"),
    re.compile(r"^([a-zA-Z0-9_-]{15,})$"),
]


def extract_drive_id(identifier: str) -> str:
    """Extract a Drive file/folder ID from a share URL or raw identifier."""
    identifier = identifier.strip()
    for pattern in _ID_PATTERNS:
        match = pattern.search(identifier)
        if match:
            return match.group(1)
    return identifier


class GoogleDriveService:
    async def build_auth_url(self, state: str) -> str:
        if not settings.google_oauth_client_id:
            raise ValueError("Google OAuth client ID is not configured")
        redirect_uri = self._redirect_uri()
        params = {
            "client_id": settings.google_oauth_client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": DRIVE_SCOPES,
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
        return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"

    async def exchange_code(self, code: str) -> dict[str, Any]:
        if not settings.google_oauth_client_secret:
            raise ValueError("Google OAuth client secret is not configured")
        payload = {
            "code": code,
            "client_id": settings.google_oauth_client_id,
            "client_secret": settings.google_oauth_client_secret,
            "redirect_uri": self._redirect_uri(),
            "grant_type": "authorization_code",
        }
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(GOOGLE_TOKEN_URL, data=payload)
            response.raise_for_status()
            return response.json()

    async def store_tokens(self, user_id: str, token_data: dict[str, Any]) -> dict[str, Any]:
        access_token = token_data.get("access_token", "")
        refresh_token = token_data.get("refresh_token", "")
        expires_in = token_data.get("expires_in", 3600)
        if not access_token:
            raise ValueError("No access token returned from Google")
        async with httpx.AsyncClient(timeout=30) as client:
            userinfo_response = await client.get(
                GOOGLE_USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"}
            )
            userinfo_response.raise_for_status()
            userinfo = userinfo_response.json()
        google_email = userinfo.get("email", "")
        expiry = datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))

        async with get_session() as session:
            result = await session.execute(
                select(GoogleDriveTokenModel).where(GoogleDriveTokenModel.user_id == user_id)
            )
            model = result.scalar_one_or_none()
            if model is None:
                model = GoogleDriveTokenModel(user_id=user_id)
                session.add(model)
            model.google_email = google_email
            model.access_token = encrypt_value(access_token)
            model.refresh_token = encrypt_value(refresh_token)
            model.token_expiry = expiry
            await session.flush()
        logger.info("google_drive_connected", user_id=user_id, email=google_email)
        return {"email": google_email, "connected": True}

    async def get_connection_status(self, user_id: str) -> dict[str, Any]:
        async with get_session() as session:
            result = await session.execute(
                select(GoogleDriveTokenModel).where(GoogleDriveTokenModel.user_id == user_id)
            )
            model = result.scalar_one_or_none()
        if model is None:
            return {"connected": False, "email": None}
        return {"connected": True, "email": model.google_email}

    async def disconnect(self, user_id: str) -> None:
        async with get_session() as session:
            result = await session.execute(
                select(GoogleDriveTokenModel).where(GoogleDriveTokenModel.user_id == user_id)
            )
            model = result.scalar_one_or_none()
            if model is not None:
                await session.delete(model)
                await session.flush()
        logger.info("google_drive_disconnected", user_id=user_id)

    async def _get_access_token(self, user_id: str) -> str:
        async with get_session() as session:
            result = await session.execute(
                select(GoogleDriveTokenModel).where(GoogleDriveTokenModel.user_id == user_id)
            )
            model = result.scalar_one_or_none()
            if model is None:
                raise ValueError("Google Drive is not connected. Connect it in the Access page first.")
            access_token = decrypt_value(model.access_token)
            refresh_token = decrypt_value(model.refresh_token)
            expiry = model.token_expiry

        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) < expiry - timedelta(minutes=5):
            return access_token

        if not refresh_token:
            raise ValueError("Google Drive refresh token is missing. Reconnect your Google account.")
        payload = {
            "client_id": settings.google_oauth_client_id,
            "client_secret": settings.google_oauth_client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(GOOGLE_TOKEN_URL, data=payload)
            response.raise_for_status()
            data = response.json()
        new_access_token = data.get("access_token", "")
        if not new_access_token:
            raise ValueError("Failed to refresh Google Drive access token")
        new_expiry = datetime.now(timezone.utc) + timedelta(seconds=int(data.get("expires_in", 3600)))

        async with get_session() as session:
            result = await session.execute(
                select(GoogleDriveTokenModel).where(GoogleDriveTokenModel.user_id == user_id)
            )
            model = result.scalar_one_or_none()
            if model is not None:
                model.access_token = encrypt_value(new_access_token)
                model.token_expiry = new_expiry
                await session.flush()
        return new_access_token

    async def share_with_user(
        self,
        user_id: str,
        resource_identifier: str,
        email: str,
        access_type: str,
    ) -> dict[str, Any]:
        if not email:
            return {"success": False, "error": "Requester email is missing"}
        file_id = extract_drive_id(resource_identifier)
        if not file_id:
            return {"success": False, "error": "Could not determine a Google Drive file or folder ID"}
        role = ROLE_MAP.get(access_type, "reader")
        access_token = await self._get_access_token(user_id)
        headers = {"Authorization": f"Bearer {access_token}"}
        body = {"role": role, "type": "user", "emailAddress": email}
        url = GOOGLE_DRIVE_PERMISSIONS_URL.format(file_id=file_id)
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    url,
                    params={"sendNotificationEmail": "true", "supportsAllDrives": "true"},
                    json=body,
                    headers=headers,
                )
                response.raise_for_status()
                permission = response.json()
            logger.info(
                "google_drive_shared",
                user_id=user_id,
                file_id=file_id,
                email=email,
                role=role,
            )
            return {
                "success": True,
                "file_id": file_id,
                "email": email,
                "role": role,
                "permission_id": permission.get("id", ""),
                "message": f"Shared Google Drive item ({file_id}) with {email} as {role}",
            }
        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                error_detail = e.response.json().get("error", {}).get("message", "")
            except Exception:
                error_detail = e.response.text[:200]
            logger.error(
                "google_drive_share_failed",
                user_id=user_id,
                file_id=file_id,
                email=email,
                status=e.response.status_code,
                detail=error_detail,
            )
            return {
                "success": False,
                "error": f"Google Drive share failed ({e.response.status_code}): {error_detail}",
            }

    def _redirect_uri(self) -> str:
        if not settings.google_oauth_redirect_uri:
            raise ValueError("Google OAuth redirect URI is not configured")
        return settings.google_oauth_redirect_uri


drive_service = GoogleDriveService()
