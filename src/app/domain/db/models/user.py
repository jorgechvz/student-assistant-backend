"""MongoDB User Domain Model."""

from datetime import datetime
from typing import Optional
from beanie import Document
from pydantic import EmailStr, Field


class UserModel(Document):
    """User Domain Model for MongoDB."""

    email: EmailStr = Field(index=True, unique=True)
    full_name: str
    password_hash: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    class Settings:  # pylint: disable=missing-class-docstring
        name = "users"
        indexes = ["email"]

    class Config:  # pylint: disable=missing-class-docstring
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "full_name": "John Doe",
                "password_hash": "hashed_password_here",
                "is_active": True,
                "is_superuser": False,
            }
        }
