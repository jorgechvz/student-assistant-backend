"""Google Token Repository"""

from typing import Optional
from app.domain.db.models.google import GoogleTokenModel


class GoogleTokenRepo:
    """Repository for Google Token operations"""

    async def save_token(self, token: GoogleTokenModel) -> GoogleTokenModel:
        """Save or update a Google token"""
        await token.save()
        return token

    async def get_token_by_user_id(self, user_id: str) -> Optional[GoogleTokenModel]:
        """Get Google token by user ID"""
        return await GoogleTokenModel.find_one(GoogleTokenModel.user_id == user_id)

    async def get_token_by_google_user_id(
        self, google_user_id: str
    ) -> Optional[GoogleTokenModel]:
        """Get Google token by Google user ID"""
        return await GoogleTokenModel.find_one(
            GoogleTokenModel.google_user_id == google_user_id
        )

    async def delete_token(self, user_id: str) -> bool:
        """Delete a Google token"""
        token = await self.get_token_by_user_id(user_id)
        if token:
            await token.delete()
            return True
        return False
