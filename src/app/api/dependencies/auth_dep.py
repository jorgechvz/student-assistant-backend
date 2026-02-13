"""Authentication dependencies for FastAPI routes."""

import logging
from typing import Annotated
from fastapi import Cookie, Depends, HTTPException, status
from app.infrastructure.adapters.security.jwt_handler import JWTHandler
from app.infrastructure.adapters.security.password_hasher import PasswordHasher
from app.infrastructure.db.repos.user_repo_beanie import UserRepoBeanie
from app.application.services.token_service import TokenService
from app.application.services.auth_service import AuthService
from app.domain.db.models.user import UserModel

_logger = logging.getLogger(__name__)


def get_jwt_handler() -> JWTHandler:
    """Get JWT handler instance"""
    return JWTHandler()


def get_password_hasher() -> PasswordHasher:
    """Get Password Hasher instance"""
    return PasswordHasher()


def get_user_repository() -> UserRepoBeanie:
    """Get User Repository instance"""
    return UserRepoBeanie()


def get_token_service(
    jwt_handler: Annotated[JWTHandler, Depends(get_jwt_handler)],
    user_repo: Annotated[UserRepoBeanie, Depends(get_user_repository)],
) -> TokenService:
    """Get Token Service instance"""
    return TokenService(jwt_handler, user_repo)


def get_auth_service(
    user_repo: Annotated[UserRepoBeanie, Depends(get_user_repository)],
    password_hasher: Annotated[PasswordHasher, Depends(get_password_hasher)],
    token_service: Annotated[TokenService, Depends(get_token_service)],
) -> AuthService:
    """Get Auth Service instance"""
    return AuthService(user_repo, password_hasher, token_service)


async def get_current_user(
    access_token: Annotated[str | None, Cookie()] = None,
    token_service: TokenService = Depends(get_token_service),
    user_repo: UserRepoBeanie = Depends(get_user_repository),
) -> UserModel:
    """Get current authenticated user from cookie"""

    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated - No token provided",
        )

    try:
        user_id = await token_service.verify_access_token(access_token)

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )

        user = await user_repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
            )

        return user
    except Exception as e:
        _logger.warning("Authentication failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
        ) from e
