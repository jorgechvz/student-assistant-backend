"""Authentication Service Module"""

from typing import Optional

from app.domain.db.repos import UserRepoInterface
from app.domain.db.models import UserModel

from app.infrastructure.adapters.security import PasswordHasher
from app.application.services.token_service import TokenService


class AuthService:
    """Service for handling user authentication."""

    def __init__(
        self,
        user_repo: UserRepoInterface,
        password_hasher: PasswordHasher,
        token_service: TokenService,
    ):
        self.user_repo = user_repo
        self.password_hasher = password_hasher
        self.token_service = token_service

    async def signup(self, email: str, password: str, full_name: str) -> Optional[dict]:
        """Register a new user and return access tokens."""

        existing_user = await self.user_repo.get_user_by_email(email)
        if existing_user:
            raise ValueError("User with this email already exists")

        hashed_password = self.password_hasher.hash(password)

        new_user = UserModel(
            email=email,
            password_hash=hashed_password,
            full_name=full_name,
            is_active=True,
        )

        saved_user = await self.user_repo.save_user(new_user)

        tokens = self.token_service.create_access_pair(str(saved_user.id))

        return {
            "user": {
                "id": str(saved_user.id),
                "email": saved_user.email,
                "full_name": saved_user.full_name,
                "is_active": saved_user.is_active,
            },
            **tokens,
        }

    async def login(self, email: str, password: str) -> Optional[dict]:
        """Authenticate user and return tokens"""
        user = await self.user_repo.get_user_by_email(email)
        if not user or not user.is_active:
            raise ValueError("Invalid email or inactive user")

        if not self.password_hasher.verify(password, user.password_hash):
            raise ValueError("Invalid password")

        tokens = self.token_service.create_access_pair(str(user.id))

        return {
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "is_active": user.is_active,
            },
            **tokens,
        }

    async def get_current_user(self, user_id: str) -> Optional[UserModel]:
        """Retrieve current user by ID"""
        user = await self.user_repo.get_user_by_id(user_id)
        if not user or not user.is_active:
            raise ValueError("User not found or inactive")
        return user

    async def refresh_access_token(self, refresh_token: str) -> Optional[dict]:
        """Refresh access token using refresh token"""
        new_tokens = await self.token_service.refresh_access_token(refresh_token)
        return new_tokens
