"""Google OAuth Routes"""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from app.application.services.google_service import GoogleService
from app.api.dependencies.google_dep import get_google_service
from app.api.dependencies.auth_dep import get_current_user
from app.domain.db.models.user import UserModel
from app.infrastructure.config.config import get_settings

router = APIRouter(prefix="/auth/google", tags=["Google Integration"])
settings = get_settings()


@router.get("/authorize")
async def authorize_google(
    current_user: Annotated[UserModel, Depends(get_current_user)],
    google_service: Annotated[GoogleService, Depends(get_google_service)],
):
    """Redirect user to Google OAuth authorization page"""

    auth_url = google_service.get_authorization_url(state=str(current_user.id))
    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def google_callback(
    code: str,
    state: str,
    google_service: Annotated[GoogleService, Depends(get_google_service)],
):
    """Handle OAuth callback from Google"""

    try:
        await google_service.exchange_code_for_token(code=code, user_id=state)

        return RedirectResponse(url=settings.frontend_google_success_url)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to connect Google: {str(e)}",
        ) from e


@router.get("/status")
async def get_google_status(
    current_user: Annotated[UserModel, Depends(get_current_user)],
    google_service: Annotated[GoogleService, Depends(get_google_service)],
):
    """Check if user has connected Google"""

    token = await google_service.get_user_token(str(current_user.id))

    if not token:
        return {"connected": False}

    return {
        "connected": True,
        "email": token.email,
        "name": token.name,
        "picture": token.picture,
        "expires_at": token.expires_at.isoformat(),
    }


@router.post("/refresh")
async def refresh_google_token(
    current_user: Annotated[UserModel, Depends(get_current_user)],
    google_service: Annotated[GoogleService, Depends(get_google_service)],
):
    """Manually refresh the Google access token"""

    try:
        await google_service.refresh_access_token(str(current_user.id))
        return {"message": "Token refreshed successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.delete("/disconnect")
async def disconnect_google(
    current_user: Annotated[UserModel, Depends(get_current_user)],
    google_service: Annotated[GoogleService, Depends(get_google_service)],
):
    """Disconnect Google integration"""

    success = await google_service.revoke_token(str(current_user.id))

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Google connection found",
        )

    return {"message": "Google disconnected successfully"}
