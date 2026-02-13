"""Notion Token Model"""

from datetime import datetime
from typing import Optional
from beanie import Document
from pydantic import Field


class NotionTokenModel(Document):
    """Model for storing Notion OAuth tokens"""

    user_id: str = Field(..., description="User ID this token belongs to")
    access_token: str = Field(..., description="Notion access token")
    refresh_token: str = Field(..., description="Notion refresh token")
    bot_id: str = Field(..., description="Notion bot ID")
    workspace_id: str = Field(..., description="Notion workspace ID")
    workspace_name: Optional[str] = Field(None, description="Notion workspace name")
    workspace_icon: Optional[str] = Field(None, description="Notion workspace icon URL")
    duplicated_template_id: Optional[str] = Field(
        None, description="ID of duplicated template page"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        """Beanie settings"""

        name = "notion_tokens"
        indexes = [
            "user_id",
            "bot_id",
        ]
