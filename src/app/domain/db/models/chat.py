"""MongoDB Chat Domain Models."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from beanie import Document
from pydantic import Field


class MessageModel(Document):
    """Individual message in a chat conversation."""

    session_id: str = Field(index=True)
    user_id: str = Field(index=True)
    role: str  # "user", "assistant", "system", "tool"
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        """Beanie settings for MessageModel."""

        name = "messages"
        indexes = [
            "session_id",
            "user_id",
            "created_at",
        ]

    class Config:  # pylint: disable=missing-class-docstring
        json_schema_extra = {
            "example": {
                "session_id": "session_123",
                "user_id": "user_456",
                "role": "user",
                "content": "What are my current courses?",
                "created_at": "2026-01-25T10:30:00Z",
            }
        }


class ChatSessionModel(Document):
    """Chat session representing a conversation thread."""

    user_id: str = Field(index=True)
    title: Optional[str] = None  # Auto-generated or user-provided
    message_count: int = 0
    last_message_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    class Settings:
        """Beanie settings for ChatSessionModel."""

        name = "chat_sessions"
        indexes = [
            "user_id",
            "created_at",
            "last_message_at",
            "is_active",
        ]

    class Config:  # pylint: disable=missing-class-docstring
        json_schema_extra = {
            "example": {
                "user_id": "user_456",
                "title": "Course Questions",
                "message_count": 5,
                "last_message_at": "2026-01-25T10:35:00Z",
                "is_active": True,
                "created_at": "2026-01-25T10:30:00Z",
            }
        }
