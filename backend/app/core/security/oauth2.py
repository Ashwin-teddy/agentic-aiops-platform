from __future__ import annotations

from typing import Any

import httpx

from app.core.config.settings import settings


class OAuth2Provider:
    def __init__(self, name: str) -> None:
        self.name = name

    async def get_authorization_url(self, state: str) -> str:
        raise NotImplementedError

    async def exchange_code(self, code: str) -> dict[str, Any]:
        raise NotImplementedError

    async def get_user_info(self, access_token: str) -> dict[str, Any]:
        raise NotImplementedError


class AzureADProvider(OAuth2Provider):
    def __init__(self) -> None:
        super().__init__("azure_ad")
        self.tenant_id = settings.azure_ad_tenant_id
        self.client_id = settings.azure_ad_client_id
        self.client_secret = settings.azure_ad_client_secret
        self.redirect_uri = settings.azure_ad_redirect_uri
        self.base_url = f"https://login.microsoftonline.com/{self.tenant_id}"

    async def get_authorization_url(self, state: str) -> str:
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "scope": "openid profile email User.Read",
            "state": state,
            "response_mode": "query",
        }
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.base_url}/oauth2/v2.0/authorize?{query}"

    async def exchange_code(self, code: str) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/oauth2/v2.0/token",
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": self.redirect_uri,
                    "scope": "openid profile email User.Read",
                },
            )
            response.raise_for_status()
            return response.json()

    async def get_user_info(self, access_token: str) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://graph.microsoft.com/v1.0/me",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            data = response.json()
            return {
                "id": data.get("id", ""),
                "email": data.get("mail") or data.get("userPrincipalName", ""),
                "display_name": data.get("displayName", ""),
                "department": data.get("department", ""),
                "job_title": data.get("jobTitle", ""),
            }
