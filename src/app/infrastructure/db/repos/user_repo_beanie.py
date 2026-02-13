"""User Repository Implementation using Beanie."""

from typing import Optional
from beanie import PydanticObjectId
from app.domain.db.models import UserModel
from app.domain.db.repos.user_repo import UserRepoInterface


class UserRepoBeanie(UserRepoInterface):
    """User Repository Implementation using Beanie ODM"""

    async def save_user(self, user: UserModel) -> UserModel:
        """Create or update user"""
        if user.id:
            user_model = await UserModel.get(PydanticObjectId(user.id))
            if not user_model:
                raise ValueError("User not found for update")

            user_model.full_name = user.full_name
            user_model.email = user.email
            user_model.password_hash = user.password_hash

            await user_model.save()
        else:
            user_model = UserModel(
                full_name=user.full_name,
                email=user.email,
                password_hash=user.password_hash,
            )
            await user_model.insert()
            user.id = str(user_model.id)
        return user

    async def get_user_by_email(self, email: str) -> Optional[UserModel]:
        """Get a user by email"""
        user = await UserModel.find_one(UserModel.email == email)
        return self._to_entity(user) if user else None

    async def get_user_by_id(self, user_id: str) -> Optional[UserModel]:
        """Get a user by ID"""
        user = await UserModel.get(PydanticObjectId(user_id))
        return self._to_entity(user) if user else None

    async def delete_user(self, email: str) -> bool:
        """Delete a user by email"""
        user = await self.get_user_by_email(email)
        if user:
            await user.delete()
            return True
        return False

    async def update_user(self, user: UserModel) -> UserModel:
        """Update user fields and return updated user"""
        from datetime import datetime

        user_model = await UserModel.get(PydanticObjectId(user.id))
        if not user_model:
            raise ValueError("User not found")

        user_model.full_name = user.full_name
        user_model.email = user.email
        user_model.password_hash = user.password_hash
        user_model.is_active = user.is_active
        user_model.updated_at = datetime.utcnow()
        await user_model.save()
        return self._to_entity(user_model)

    async def delete_user_by_id(self, user_id: str) -> bool:
        """Delete a user by ID"""
        user = await UserModel.get(PydanticObjectId(user_id))
        if user:
            await user.delete()
            return True
        return False

    def _to_entity(self, user_model: UserModel) -> UserModel:
        """Convert Beanie model to domain entity"""
        return UserModel(
            id=str(user_model.id),
            full_name=user_model.full_name,
            email=user_model.email,
            password_hash=user_model.password_hash,
            is_active=user_model.is_active,
            created_at=user_model.created_at,
            updated_at=user_model.updated_at,
        )
