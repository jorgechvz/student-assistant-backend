"""Google OAuth Service"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.parse import urlencode
import httpx
from app.infrastructure.config.config import get_settings
from app.infrastructure.adapters.resources.google_repo import GoogleTokenRepo
from app.domain.db.models.google import GoogleTokenModel


class GoogleService:
    """Service for handling Google OAuth operations"""

    def __init__(self, google_token_repo: GoogleTokenRepo):
        self.settings = get_settings()
        self.google_token_repo = google_token_repo
        self.token_url = "https://oauth2.googleapis.com/token"
        self.userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"

        self.scopes = [
            "https://www.googleapis.com/auth/calendar",
            "https://www.googleapis.com/auth/calendar.events",
            "https://www.googleapis.com/auth/calendar.settings.readonly",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
        ]

    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """Generate the Google OAuth authorization URL"""
        params = {
            "client_id": self.settings.google_client_id,
            "redirect_uri": self.settings.google_redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.scopes),
            "access_type": "offline",
            "prompt": "consent",
        }

        if state:
            params["state"] = state

        return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"

    async def exchange_code_for_token(
        self, code: str, user_id: str
    ) -> GoogleTokenModel:
        """Exchange authorization code for access token"""

        data = {
            "client_id": self.settings.google_client_id,
            "client_secret": self.settings.google_client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.settings.google_redirect_uri,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(self.token_url, data=data, timeout=30.0)

            if response.status_code != 200:
                error_data = response.json()
                raise ValueError(
                    f"Failed to exchange code: {error_data.get('error_description', 'Unknown error')}"
                )

            token_data = response.json()

        user_info = await self._get_user_info(token_data["access_token"])

        expires_in = token_data.get("expires_in", 3600)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

        google_token = GoogleTokenModel(
            user_id=user_id,
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            token_type=token_data.get("token_type", "Bearer"),
            expires_at=expires_at,
            scope=token_data.get("scope", " ".join(self.scopes)),
            google_user_id=user_info.get("id"),
            email=user_info.get("email"),
            name=user_info.get("name"),
            picture=user_info.get("picture"),
        )

        return await self.google_token_repo.save_token(google_token)

    async def _get_user_info(self, access_token: str) -> dict:
        """Get user info from Google"""
        headers = {"Authorization": f"Bearer {access_token}"}

        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.userinfo_url, headers=headers, timeout=10.0
            )

            if response.status_code != 200:
                return {}

            return response.json()

    async def refresh_access_token(self, user_id: str) -> GoogleTokenModel:
        """Refresh the Google access token"""

        token = await self.google_token_repo.get_token_by_user_id(user_id)
        if not token:
            raise ValueError("No Google token found for user")

        if not token.refresh_token:
            raise ValueError("No refresh token available")

        data = {
            "client_id": self.settings.google_client_id,
            "client_secret": self.settings.google_client_secret,
            "refresh_token": token.refresh_token,
            "grant_type": "refresh_token",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(self.token_url, data=data, timeout=30.0)

            if response.status_code != 200:
                error_data = response.json()
                raise ValueError(
                    f"Failed to refresh token: {error_data.get('error_description', 'Unknown error')}"
                )

            token_data = response.json()

        expires_in = token_data.get("expires_in", 3600)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

        token.access_token = token_data["access_token"]
        token.expires_at = expires_at
        if "refresh_token" in token_data:
            token.refresh_token = token_data["refresh_token"]

        return await self.google_token_repo.save_token(token)

    async def get_valid_access_token(self, user_id: str) -> str:
        """Get a valid access token, refreshing if necessary."""
        token = await self.google_token_repo.get_token_by_user_id(user_id)

        if not token:
            raise ValueError(f"No Google token found for user {user_id}")

        now = datetime.now(timezone.utc)

        expires_at = token.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if expires_at <= now + timedelta(minutes=5):
            refreshed_token = await self.refresh_access_token(user_id)
            return refreshed_token.access_token

        return token.access_token

    async def make_google_request(
        self,
        user_id: str,
        method: str,
        endpoint: str,
        data: Optional[dict] = None,
        params: Optional[dict] = None,
    ) -> dict:
        """
        Make an authenticated request to Google API with automatic token refresh.

        Args:
            user_id: The user's ID
            method: HTTP method (GET, POST, PATCH, DELETE)
            endpoint: Google API endpoint (e.g., "/calendar/v3/calendars/primary/events")
            data: Optional request body data (JSON)
            params: Optional query parameters for the request

        Returns:
            Response data from Google API
        """

        access_token = await self.get_valid_access_token(user_id)

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        url = f"https://www.googleapis.com{endpoint}"

        async with httpx.AsyncClient() as client:
            response = await self._execute_request(
                client, method, url, headers, data, params
            )

            if response.status_code == 401:
                try:
                    await self.refresh_access_token(user_id)
                    access_token = await self.get_valid_access_token(user_id)
                    headers["Authorization"] = f"Bearer {access_token}"
                    response = await self._execute_request(
                        client, method, url, headers, data, params
                    )
                except Exception as e:
                    raise ValueError(
                        "Token refresh failed. User needs to re-authorize."
                    ) from e

            if response.status_code not in [200, 201, 204]:
                error_data = response.json() if response.text else {}
                raise ValueError(
                    f"Google API error: {error_data.get('error', {}).get('message', 'Unknown error')}"
                )

            return response.json() if response.text else {}

    @staticmethod
    async def _execute_request(
        client: httpx.AsyncClient,
        method: str,
        url: str,
        headers: dict,
        data: Optional[dict] = None,
        params: Optional[dict] = None,
    ) -> httpx.Response:
        """Execute an HTTP request with the given parameters."""
        method_upper = method.upper()
        if method_upper == "GET":
            return await client.get(url, headers=headers, params=params, timeout=30.0)
        if method_upper == "POST":
            return await client.post(
                url, headers=headers, json=data, params=params, timeout=30.0
            )
        if method_upper == "PATCH":
            return await client.patch(
                url, headers=headers, json=data, params=params, timeout=30.0
            )
        if method_upper == "DELETE":
            return await client.delete(
                url, headers=headers, params=params, timeout=30.0
            )
        raise ValueError(f"Unsupported HTTP method: {method}")

    async def get_user_token(self, user_id: str) -> Optional[GoogleTokenModel]:
        """Get Google token for a user"""
        return await self.google_token_repo.get_token_by_user_id(user_id)

    async def revoke_token(self, user_id: str) -> bool:
        """Revoke/delete Google token for a user"""
        token = await self.google_token_repo.get_token_by_user_id(user_id)

        if token:
            try:
                async with httpx.AsyncClient() as client:
                    await client.post(
                        f"https://oauth2.googleapis.com/revoke?token={token.access_token}",
                        timeout=10.0,
                    )
            except Exception as e:
                raise ValueError("Failed to revoke token with Google") from e

            return await self.google_token_repo.delete_token(user_id)

        return False
