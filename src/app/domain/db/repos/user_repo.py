"""User Repository Interface Implementation."""

from abc import ABC, abstractmethod
from typing import Optional
from app.domain.db.models import UserModel


class UserRepoInterface(ABC):
    """User Repository Interface"""

    @abstractmethod
    async def save_user(self, user: UserModel) -> UserModel:
        """Create or update user"""

    @abstractmethod
    async def get_user_by_email(self, email: str) -> Optional[UserModel]:
        """Get a user by email"""

    @abstractmethod
    async def get_user_by_id(self, user_id: str) -> Optional[UserModel]:
        """Get a user by ID"""

    @abstractmethod
    async def delete_user(self, email: str) -> bool:
        """Delete a user by email"""

    @abstractmethod
    async def update_user(self, user: UserModel) -> UserModel:
        """Update user fields and return updated user"""

    @abstractmethod
    async def delete_user_by_id(self, user_id: str) -> bool:
        """Delete a user by ID"""
