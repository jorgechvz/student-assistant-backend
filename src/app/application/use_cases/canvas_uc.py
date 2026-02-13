"""Canvas Use Cases - Business logic for Canvas operations."""

from app.domain.db.models.canvas import CanvasTokenModel
from app.infrastructure.adapters.resources.canvas_repo import CanvasRepository


class CanvasUseCase:
    """Use case for Canvas integration operations."""

    async def setup_canvas(
        self,
        user_id: str,
        canvas_base_url: str,
        access_token: str,
    ) -> str:
        """Set up Canvas integration for a user.

        Args:
            user_id: User ID
            canvas_base_url: Canvas LMS base URL
            access_token: Canvas API access token

        Returns:
            Canvas user name

        Raises:
            ValueError: If token is invalid
        """

        canvas_repo = CanvasRepository(canvas_base_url, access_token)

        try:
            user_profile = canvas_repo._call_api("/users/self")
            canvas_user_id = str(user_profile.get("id", ""))
            canvas_user_name = user_profile.get("name", "")
        except Exception as e:
            raise ValueError(f"Invalid Canvas token or URL: {str(e)}") from e

        existing_token = await CanvasTokenModel.find_one(
            CanvasTokenModel.user_id == user_id
        )

        if existing_token:
            existing_token.canvas_base_url = canvas_base_url
            existing_token.access_token = access_token
            existing_token.canvas_user_id = canvas_user_id
            existing_token.canvas_user_name = canvas_user_name
            await existing_token.save()
        else:
            canvas_token = CanvasTokenModel(
                user_id=user_id,
                canvas_base_url=canvas_base_url,
                access_token=access_token,
                canvas_user_id=canvas_user_id,
                canvas_user_name=canvas_user_name,
            )
            await canvas_token.save()

        return canvas_user_name

    async def get_canvas_status(self, user_id: str) -> dict:
        """Check Canvas connection status for a user.

        Args:
            user_id: User ID

        Returns:
            Dict with connected status and details
        """
        canvas_token = await CanvasTokenModel.find_one(
            CanvasTokenModel.user_id == user_id
        )

        if canvas_token:
            return {
                "connected": True,
                "canvas_base_url": canvas_token.canvas_base_url,
                "canvas_user_name": canvas_token.canvas_user_name,
            }
        else:
            return {"connected": False}

    async def disconnect_canvas(self, user_id: str) -> bool:
        """Disconnect Canvas integration for a user.

        Args:
            user_id: User ID

        Returns:
            True if disconnected, False if no integration found
        """
        canvas_token = await CanvasTokenModel.find_one(
            CanvasTokenModel.user_id == user_id
        )

        if not canvas_token:
            return False

        await canvas_token.delete()
        return True

    async def get_upcoming_assignments(self, user_id: str) -> list[dict]:
        """Get all upcoming assignments across all courses for the user.

        Args:
            user_id: User ID

        Returns:
            List of upcoming assignments with course info, sorted by due date

        Raises:
            ValueError: If Canvas integration is not set up
        """
        canvas_token = await CanvasTokenModel.find_one(
            CanvasTokenModel.user_id == user_id
        )

        if not canvas_token:
            raise ValueError("Canvas integration not set up")

        canvas_repo = CanvasRepository(
            canvas_token.canvas_base_url, canvas_token.access_token
        )
        return canvas_repo.get_all_upcoming_assignments()
