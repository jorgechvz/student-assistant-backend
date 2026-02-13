"""Notion OAuth Service"""

import base64
from typing import Optional
import httpx
from app.infrastructure.config.config import get_settings
from app.infrastructure.adapters.resources.notion_repo import NotionTokenRepo
from app.domain.db.models.notion import NotionTokenModel


class NotionService:
    """Service for handling Notion OAuth operations"""

    def __init__(self, notion_token_repo: NotionTokenRepo):
        self.settings = get_settings()
        self.notion_token_repo = notion_token_repo
        self.token_url = "https://api.notion.com/v1/oauth/token"

    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """Generate the Notion OAuth authorization URL"""
        base_url = "https://api.notion.com/v1/oauth/authorize"
        params = {
            "client_id": self.settings.notion_client_id,
            "redirect_uri": self.settings.notion_redirect_uri,
            "response_type": "code",
            "owner": "user",
        }

        if state:
            params["state"] = state

        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}?{query_string}"

    async def exchange_code_for_token(
        self, code: str, user_id: str
    ) -> NotionTokenModel:
        """Exchange authorization code for access token"""

        credentials = (
            f"{self.settings.notion_client_id}:{self.settings.notion_client_secret}"
        )
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        body = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.settings.notion_redirect_uri,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url, headers=headers, json=body, timeout=30.0
            )

            if response.status_code != 200:
                error_data = response.json()
                raise ValueError(
                    f"Failed to exchange code: {error_data.get('error', 'Unknown error')}"
                )

            data = response.json()

        notion_token = NotionTokenModel(
            user_id=user_id,
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            bot_id=data["bot_id"],
            workspace_id=data["workspace_id"],
            workspace_name=data.get("workspace_name"),
            workspace_icon=data.get("workspace_icon"),
            duplicated_template_id=data.get("duplicated_template_id"),
        )

        return await self.notion_token_repo.save_token(notion_token)

    async def refresh_access_token(self, user_id: str) -> NotionTokenModel:
        """Refresh the Notion access token"""

        token = await self.notion_token_repo.get_token_by_user_id(user_id)
        if not token:
            raise ValueError("No Notion token found for user")

        credentials = (
            f"{self.settings.notion_client_id}:{self.settings.notion_client_secret}"
        )
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        body = {
            "grant_type": "refresh_token",
            "refresh_token": token.refresh_token,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url, headers=headers, json=body, timeout=30.0
            )

            if response.status_code != 200:
                error_data = response.json()
                raise ValueError(
                    f"Failed to refresh token: {error_data.get('error', 'Unknown error')}"
                )

            data = response.json()

        token.access_token = data["access_token"]
        token.refresh_token = data.get("refresh_token", token.refresh_token)

        return await self.notion_token_repo.save_token(token)

    async def get_user_token(self, user_id: str) -> Optional[NotionTokenModel]:
        """Get Notion token for a user"""
        return await self.notion_token_repo.get_token_by_user_id(user_id)

    async def revoke_token(self, user_id: str) -> bool:
        """Revoke/delete Notion token for a user"""
        return await self.notion_token_repo.delete_token(user_id)
