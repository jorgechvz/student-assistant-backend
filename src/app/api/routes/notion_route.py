"""Notion OAuth Routes"""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from app.application.services.notion_service import NotionService
from app.api.dependencies.notion_dep import get_notion_service
from app.api.dependencies.auth_dep import get_current_user
from app.domain.db.models.user import UserModel
from app.infrastructure.config.config import get_settings

router = APIRouter(prefix="/auth/notion", tags=["Notion Integration"])
settings = get_settings()


@router.get("/authorize")
async def authorize_notion(
    current_user: Annotated[UserModel, Depends(get_current_user)],
    notion_service: Annotated[NotionService, Depends(get_notion_service)],
):
    """Redirect user to Notion OAuth authorization page"""

    auth_url = notion_service.get_authorization_url(state=str(current_user.id))
    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def notion_callback(
    code: str,
    state: str,
    notion_service: Annotated[NotionService, Depends(get_notion_service)],
):
    """Handle OAuth callback from Notion"""

    try:
        await notion_service.exchange_code_for_token(code=code, user_id=state)

        return RedirectResponse(url=settings.frontend_success_url)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to connect Notion: {str(e)}",
        ) from e


@router.get("/status")
async def get_notion_status(
    current_user: Annotated[UserModel, Depends(get_current_user)],
    notion_service: Annotated[NotionService, Depends(get_notion_service)],
):
    """Check if user has connected Notion"""

    token = await notion_service.get_user_token(str(current_user.id))

    if not token:
        return {"connected": False}

    return {
        "connected": True,
        "workspace_name": token.workspace_name,
        "workspace_icon": token.workspace_icon,
    }


@router.delete("/disconnect")
async def disconnect_notion(
    current_user: Annotated[UserModel, Depends(get_current_user)],
    notion_service: Annotated[NotionService, Depends(get_notion_service)],
):
    """Disconnect Notion integration"""

    success = await notion_service.revoke_token(str(current_user.id))

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Notion connection found",
        )

    return {"message": "Notion disconnected successfully"}
