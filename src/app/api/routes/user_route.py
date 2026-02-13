"""User Settings Routes"""

import logging
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.domain.db.models.user import UserModel
from app.api.dependencies.auth_dep import (
    get_current_user,
    get_user_repository,
    get_password_hasher,
)
from app.infrastructure.db.repos.user_repo_beanie import UserRepoBeanie
from app.infrastructure.adapters.security.password_hasher import PasswordHasher
from app.application.services.user_settings_service import UserSettingsService
from app.shared.schemas.user import (
    UpdateProfileRequest,
    ChangePasswordRequest,
    DeleteAccountRequest,
    UserProfileResponse,
    IntegrationStatusResponse,
)

_logger = logging.getLogger(__name__)
router = APIRouter(prefix="/user", tags=["User Settings"])


def get_user_settings_service(
    user_repo: Annotated[UserRepoBeanie, Depends(get_user_repository)],
    password_hasher: Annotated[PasswordHasher, Depends(get_password_hasher)],
) -> UserSettingsService:
    """Get User Settings Service instance"""
    return UserSettingsService(user_repo, password_hasher)


@router.get("/profile", response_model=UserProfileResponse)
async def get_profile(
    current_user: Annotated[UserModel, Depends(get_current_user)],
    service: Annotated[UserSettingsService, Depends(get_user_settings_service)],
):
    """Get current user's full profile with integration status."""
    integrations = await service.get_integrations_status(str(current_user.id))

    return UserProfileResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        created_at=current_user.created_at.isoformat(),
        has_canvas=integrations["canvas"],
        has_google=integrations["google"],
        has_notion=integrations["notion"],
    )


@router.patch("/profile", response_model=UserProfileResponse)
async def update_profile(
    request: UpdateProfileRequest,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    service: Annotated[UserSettingsService, Depends(get_user_settings_service)],
):
    """Update user profile (name and/or email)."""
    try:
        updated_user = await service.update_profile(
            user_id=str(current_user.id),
            full_name=request.full_name,
            email=request.email,
        )

        integrations = await service.get_integrations_status(str(current_user.id))

        return UserProfileResponse(
            id=str(updated_user.id),
            email=updated_user.email,
            full_name=updated_user.full_name,
            is_active=updated_user.is_active,
            created_at=updated_user.created_at.isoformat(),
            has_canvas=integrations["canvas"],
            has_google=integrations["google"],
            has_notion=integrations["notion"],
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    request: ChangePasswordRequest,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    service: Annotated[UserSettingsService, Depends(get_user_settings_service)],
):
    """Change user password."""
    try:
        await service.change_password(
            user_id=str(current_user.id),
            current_password=request.current_password,
            new_password=request.new_password,
        )
        return {"message": "Password changed successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.delete("/account", status_code=status.HTTP_200_OK)
async def delete_account(
    request: DeleteAccountRequest,
    response: Response,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    service: Annotated[UserSettingsService, Depends(get_user_settings_service)],
):
    """Delete user account and all associated data. Requires password confirmation."""
    try:
        await service.delete_account(
            user_id=str(current_user.id),
            password=request.password,
        )

        response.delete_cookie(key="access_token")
        response.delete_cookie(key="refresh_token")

        return {"message": "Account deleted successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.get("/integrations", response_model=IntegrationStatusResponse)
async def get_integrations(
    current_user: Annotated[UserModel, Depends(get_current_user)],
    service: Annotated[UserSettingsService, Depends(get_user_settings_service)],
):
    """Get status of all connected integrations."""
    status_data = await service.get_integrations_status(str(current_user.id))
    return IntegrationStatusResponse(**status_data)


@router.delete("/integrations/{integration}")
async def disconnect_integration(
    integration: str,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    service: Annotated[UserSettingsService, Depends(get_user_settings_service)],
):
    """Disconnect a specific integration (canvas, google, or notion)."""
    try:
        await service.disconnect_integration(
            user_id=str(current_user.id),
            integration=integration,
        )
        return {"message": f"{integration.capitalize()} disconnected successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
