"""Notion Token Repository"""

from typing import Optional
from app.domain.db.models.notion import NotionTokenModel


class NotionTokenRepo:
    """Repository for Notion Token operations"""

    async def save_token(self, token: NotionTokenModel) -> NotionTokenModel:
        """Save or update a Notion token"""
        await token.save()
        return token

    async def get_token_by_user_id(self, user_id: str) -> Optional[NotionTokenModel]:
        """Get Notion token by user ID"""
        return await NotionTokenModel.find_one(NotionTokenModel.user_id == user_id)

    async def get_token_by_bot_id(self, bot_id: str) -> Optional[NotionTokenModel]:
        """Get Notion token by bot ID"""
        return await NotionTokenModel.find_one(NotionTokenModel.bot_id == bot_id)

    async def delete_token(self, user_id: str) -> bool:
        """Delete a Notion token"""
        token = await self.get_token_by_user_id(user_id)
        if token:
            await token.delete()
            return True
        return False
