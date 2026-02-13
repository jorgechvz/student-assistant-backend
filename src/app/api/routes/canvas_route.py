"""Canvas LMS API Routes."""

from typing import Optional

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, HttpUrl

from app.domain.db.models.user import UserModel
from app.api.dependencies.auth_dep import get_current_user
from app.api.dependencies.chat_dep import get_canvas_use_case
from app.application.use_cases.canvas_uc import CanvasUseCase

__logger = logging.getLogger(__name__)

router = APIRouter(prefix="/canvas", tags=["Canvas"])


class CanvasSetupRequest(BaseModel):
    """Request model for setting up Canvas integration."""

    canvas_base_url: HttpUrl = Field(
        ..., description="Canvas LMS base URL (e.g., https://canvas.instructure.com)"
    )
    access_token: str = Field(..., min_length=10, description="Canvas API access token")


class CanvasStatusResponse(BaseModel):
    """Response model for Canvas connection status."""

    connected: bool
    canvas_base_url: Optional[str] = None
    canvas_user_name: Optional[str] = None


class UpcomingCanvasAssignment(BaseModel):
    """Model for upcoming Canvas assignment."""

    course: str
    assignment: str
    description: Optional[str] = None
    due_at: Optional[str] = None
    points: Optional[float] = None
    html_url: Optional[str] = None


@router.get("/upcoming-assignments", response_model=list[UpcomingCanvasAssignment])
async def get_upcoming_assignments(
    current_user: UserModel = Depends(get_current_user),
    canvas_uc: CanvasUseCase = Depends(get_canvas_use_case),
):
    """
    Get upcoming Canvas assignments across all courses.

    Returns a list of upcoming assignments with course name, assignment name,
    due date, points, and description.
    """
    try:
        assignments_data = await canvas_uc.get_upcoming_assignments(
            user_id=str(current_user.id)
        )

        return [UpcomingCanvasAssignment(**a) for a in assignments_data]

    except Exception as e:
        __logger.error(
            "Failed to fetch upcoming Canvas assignments: %s", e, exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch upcoming Canvas assignments",
        ) from e


@router.post("/setup")
async def setup_canvas(
    request: CanvasSetupRequest,
    current_user: UserModel = Depends(get_current_user),
    canvas_uc: CanvasUseCase = Depends(get_canvas_use_case),
):
    """
    Set up Canvas LMS integration by providing API token.

    To get your Canvas API token:
    1. Log in to Canvas
    2. Go to Account → Settings
    3. Scroll to "Approved Integrations"
    4. Click "+ New Access Token"
    5. Copy the generated token

    - **canvas_base_url**: Your Canvas instance URL (e.g., https://canvas.instructure.com)
    - **access_token**: Your Canvas API access token
    """

    try:
        canvas_user_name = await canvas_uc.setup_canvas(
            user_id=str(current_user.id),
            canvas_base_url=str(request.canvas_base_url),
            access_token=request.access_token,
        )

        return {
            "message": "Canvas integration configured successfully",
            "canvas_user_name": canvas_user_name,
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        ) from e

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set up Canvas: {str(e)}",
        ) from e


@router.get("/status", response_model=CanvasStatusResponse)
async def get_canvas_status(
    current_user: UserModel = Depends(get_current_user),
    canvas_uc: CanvasUseCase = Depends(get_canvas_use_case),
):
    """
    Check if Canvas integration is connected.
    """
    try:
        status_data = await canvas_uc.get_canvas_status(user_id=str(current_user.id))

        return CanvasStatusResponse(**status_data)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check Canvas status",
        ) from e


@router.delete("/disconnect")
async def disconnect_canvas(
    current_user: UserModel = Depends(get_current_user),
    canvas_uc: CanvasUseCase = Depends(get_canvas_use_case),
):
    """
    Disconnect Canvas integration by removing stored token.
    """
    try:
        disconnected = await canvas_uc.disconnect_canvas(user_id=str(current_user.id))

        if not disconnected:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No Canvas integration found",
            )

        return {"message": "Canvas integration disconnected successfully"}

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disconnect Canvas",
        ) from e
