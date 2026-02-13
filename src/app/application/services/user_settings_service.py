"""User Settings Service Module"""

import logging
from typing import Optional

from app.domain.db.repos import UserRepoInterface
from app.domain.db.models import UserModel
from app.domain.db.models.canvas import CanvasTokenModel
from app.domain.db.models.google import GoogleTokenModel
from app.domain.db.models.notion import NotionTokenModel
from app.domain.db.models.chat import ChatSessionModel, MessageModel
from app.infrastructure.adapters.security import PasswordHasher

_logger = logging.getLogger(__name__)


class UserSettingsService:
    """Service for managing user profile and account settings."""

    def __init__(
        self,
        user_repo: UserRepoInterface,
        password_hasher: PasswordHasher,
    ):
        self.user_repo = user_repo
        self.password_hasher = password_hasher

    async def get_profile(self, user_id: str) -> UserModel:
        """Get user profile by ID."""
        user = await self.user_repo.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        return user

    async def update_profile(
        self,
        user_id: str,
        full_name: Optional[str] = None,
        email: Optional[str] = None,
    ) -> UserModel:
        """Update user profile fields."""
        user = await self.user_repo.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        if email and email != user.email:
            existing = await self.user_repo.get_user_by_email(email)
            if existing:
                raise ValueError("Email already in use by another account")
            user.email = email

        if full_name:
            user.full_name = full_name

        updated_user = await self.user_repo.update_user(user)
        return updated_user

    async def change_password(
        self, user_id: str, current_password: str, new_password: str
    ) -> bool:
        """Change user password after verifying current one."""
        user = await self.user_repo.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        if not self.password_hasher.verify(current_password, user.password_hash):
            raise ValueError("Current password is incorrect")

        user.password_hash = self.password_hasher.hash(new_password)
        await self.user_repo.update_user(user)
        _logger.info("Password changed for user %s", user_id)
        return True

    async def delete_account(self, user_id: str, password: str) -> bool:
        """Delete user account and all associated data after password verification."""
        user = await self.user_repo.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        if not self.password_hasher.verify(password, user.password_hash):
            raise ValueError("Incorrect password")

        # Delete all integration tokens
        await CanvasTokenModel.find(
            CanvasTokenModel.user_id == user_id
        ).delete()
        await GoogleTokenModel.find(
            GoogleTokenModel.user_id == user_id
        ).delete()
        await NotionTokenModel.find(
            NotionTokenModel.user_id == user_id
        ).delete()

        # Delete all chat sessions and messages
        await MessageModel.find(
            MessageModel.user_id == user_id
        ).delete()
        await ChatSessionModel.find(
            ChatSessionModel.user_id == user_id
        ).delete()

        # Delete the user
        deleted = await self.user_repo.delete_user_by_id(user_id)
        if deleted:
            _logger.info("Account deleted for user %s", user_id)
        return deleted

    async def get_integrations_status(self, user_id: str) -> dict:
        """Get status of all connected integrations for the user."""
        canvas_token = await CanvasTokenModel.find_one(
            CanvasTokenModel.user_id == user_id
        )
        google_token = await GoogleTokenModel.find_one(
            GoogleTokenModel.user_id == user_id
        )
        notion_token = await NotionTokenModel.find_one(
            NotionTokenModel.user_id == user_id
        )

        return {
            "canvas": canvas_token is not None,
            "google": google_token is not None,
            "notion": notion_token is not None,
            "canvas_user_name": (
                canvas_token.canvas_user_name if canvas_token else None
            ),
            "google_email": google_token.email if google_token else None,
            "notion_workspace_name": (
                notion_token.workspace_name if notion_token else None
            ),
        }

    async def disconnect_integration(
        self, user_id: str, integration: str
    ) -> bool:
        """Disconnect a specific integration by deleting its token."""
        match integration:
            case "canvas":
                result = await CanvasTokenModel.find(
                    CanvasTokenModel.user_id == user_id
                ).delete()
            case "google":
                result = await GoogleTokenModel.find(
                    GoogleTokenModel.user_id == user_id
                ).delete()
            case "notion":
                result = await NotionTokenModel.find(
                    NotionTokenModel.user_id == user_id
                ).delete()
            case _:
                raise ValueError(
                    f"Unknown integration: {integration}. "
                    "Valid options: canvas, google, notion"
                )

        _logger.info(
            "Disconnected %s for user %s (deleted: %s)",
            integration,
            user_id,
            result,
        )
        return True
