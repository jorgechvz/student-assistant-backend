"""User Settings Schemas"""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UpdateProfileRequest(BaseModel):
    """Request to update user profile info."""

    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None


class ChangePasswordRequest(BaseModel):
    """Request to change user password."""

    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)


class DeleteAccountRequest(BaseModel):
    """Request to delete user account (requires password confirmation)."""

    password: str = Field(..., min_length=1)


class UserProfileResponse(BaseModel):
    """Full user profile response."""

    id: str
    email: str
    full_name: str
    is_active: bool
    created_at: str
    has_canvas: bool = False
    has_google: bool = False
    has_notion: bool = False


class IntegrationStatusResponse(BaseModel):
    """Response showing connected integrations."""

    canvas: bool = False
    google: bool = False
    notion: bool = False
    canvas_user_name: Optional[str] = None
    google_email: Optional[str] = None
    notion_workspace_name: Optional[str] = None
