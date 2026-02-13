"""Authentication Routes"""

import logging
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from app.shared.schemas.auth import (
    SignUpRequest,
    LoginRequest,
    LoginResponse,
    UserResponse,
)
from app.application.services.auth_service import AuthService
from app.api.dependencies.auth_dep import get_auth_service, get_current_user
from app.domain.db.models.user import UserModel
from app.infrastructure.config.config import get_settings

_logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()


@router.post(
    "/signup", response_model=LoginResponse, status_code=status.HTTP_201_CREATED
)
async def signup(
    request: SignUpRequest,
    response: Response,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    """Register a new user"""
    try:
        result = await auth_service.signup(
            email=request.email, password=request.password, full_name=request.full_name
        )

        _set_auth_cookies(response, result["access_token"], result["refresh_token"])

        return LoginResponse(**result)

    except ValueError as e:
        _logger.warning("Signup failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except Exception as e:
        _logger.error("Signup unexpected error: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    response: Response,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    """Login user"""
    try:
        result = await auth_service.login(
            email=request.email, password=request.password
        )

        # Set cookies
        _set_auth_cookies(response, result["access_token"], result["refresh_token"])

        return LoginResponse(**result)

    except ValueError as e:
        _logger.warning("Login failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)
        ) from e


@router.post("/logout")
async def logout(response: Response):
    """Logout user by clearing cookies"""
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
    return {"message": "Successfully logged out"}


@router.post("/refresh", response_model=LoginResponse)
async def refresh(
    request: Request,
    response: Response,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    """Refresh access token using refresh token"""
    try:
        # Get refresh token from cookie
        refresh_token = request.cookies.get("refresh_token")

        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token not found",
            )

        # Generate new tokens
        result = await auth_service.refresh_access_token(refresh_token)

        # Set new cookies
        _set_auth_cookies(response, result["access_token"], result["refresh_token"])

        return LoginResponse(**result)

    except ValueError as e:
        _logger.warning("Token refresh failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)
        ) from e


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: Annotated[UserModel, Depends(get_current_user)]):
    """Get current authenticated user"""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
    )


@router.get("/token")
async def get_token(
    current_user: Annotated[UserModel, Depends(get_current_user)],
    request: Request,
):
    """Return access token from cookie for streaming auth."""
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"access_token": token}


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str):
    """Helper to set authentication cookies"""
    # Access token cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=settings.cookie_httponly,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.jwt_access_token_expire_minutes * 60,
        path="/",
        domain=settings.cookie_domain,
    )

    # Refresh token cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=settings.cookie_httponly,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.jwt_refresh_token_expire_days * 24 * 60 * 60,
        path="/",
        domain=settings.cookie_domain,
    )
