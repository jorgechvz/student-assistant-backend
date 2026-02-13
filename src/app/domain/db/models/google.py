"""Google Token Model"""

from datetime import datetime
from typing import Optional
from beanie import Document
from pydantic import Field


class GoogleTokenModel(Document):
    """Model for storing Google OAuth tokens"""

    user_id: str = Field(..., description="User ID this token belongs to")
    access_token: str = Field(..., description="Google access token")
    refresh_token: str = Field(..., description="Google refresh token")
    token_type: str = Field(default="Bearer", description="Token type")
    expires_at: datetime = Field(..., description="Token expiration time")
    scope: str = Field(..., description="Granted scopes")

    google_user_id: Optional[str] = Field(None, description="Google user ID")
    email: Optional[str] = Field(None, description="Google account email")
    name: Optional[str] = Field(None, description="User's name")
    picture: Optional[str] = Field(None, description="Profile picture URL")

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        """Beanie settings"""

        name = "google_tokens"
        indexes = [
            "user_id",
            "google_user_id",
        ]
