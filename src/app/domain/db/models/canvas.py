"""MongoDB Canvas Token Model."""

from typing import Optional
from beanie import Document
from pydantic import Field


class CanvasTokenModel(Document):
    """Canvas LMS token model for MongoDB."""

    user_id: str = Field(index=True)
    canvas_base_url: str  # e.g., "https://canvas.instructure.com"
    access_token: str
    canvas_user_id: Optional[str] = None
    canvas_user_name: Optional[str] = None

    class Settings:
        name = "canvas_tokens"
        indexes = [
            "user_id",
        ]

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_123",
                "canvas_base_url": "https://canvas.instructure.com",
                "access_token": "token_here",
                "canvas_user_id": "123456",
                "canvas_user_name": "John Doe",
            }
        }
