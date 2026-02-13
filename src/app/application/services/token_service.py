"""Token service module"""

from typing import Optional
from jwt import PyJWTError, ExpiredSignatureError
from app.infrastructure.adapters.security import JWTHandler
from app.domain.db.repos.user_repo import UserRepoInterface


class TokenService:
    """Application service for handling JWT tokens."""

    def __init__(self, jwt_handler: JWTHandler, user_repo: UserRepoInterface):
        self.jwt_handler = jwt_handler
        self.user_repo = user_repo

    def create_access_pair(self, user_id: str) -> dict[str, str]:
        """Create access and refresh tokens for a user."""
        return {
            "access_token": self.jwt_handler.create_access_token(user_id),
            "refresh_token": self.jwt_handler.create_refresh_token(user_id),
            "token_type": "bearer",
        }

    async def refresh_access_token(self, refresh_token: str) -> dict[str, str]:
        """Generate a new access token using a refresh token."""
        try:
            payload = self.jwt_handler.verify_token(refresh_token, token_type="refresh")
            user_id: str = payload.get("sub")

            user = await self.user_repo.get_user_by_id(user_id)
            if not user or not user.is_active:
                raise ValueError("User not found or inactive")

            return {
                "access_token": self.jwt_handler.create_access_token(user_id),
                "refresh_token": self.jwt_handler.create_refresh_token(user_id),
                "token_type": "bearer",
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "full_name": user.full_name,
                    "is_active": user.is_active,
                },
            }
        except ExpiredSignatureError as e:
            raise ValueError("Refresh token expired") from e
        except PyJWTError as e:
            raise ValueError("Invalid refresh token") from e
        except Exception as e:
            raise ValueError("Invalid refresh token") from e

    async def verify_access_token(self, token: str) -> Optional[str]:
        """Verify an access token and return the user ID if valid."""
        try:
            payload = self.jwt_handler.verify_token(token, token_type="access")
            user_id: str = payload.get("sub")
            return user_id
        except Exception as e:
            raise ValueError("Invalid refresh token") from e
