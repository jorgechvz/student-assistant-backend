"""Chat Use Cases - Business logic for chat operations."""

from typing import Any, Dict, List, Optional
from app.application.services.agent_service import AgentService


class ChatUseCase:
    """Use case for chat operations."""

    def __init__(self, agent_service: AgentService):
        """Initialize Chat Use Case.

        Args:
            agent_service: Agent service for orchestrating chat
        """
        self.agent_service = agent_service

    async def send_message(
        self,
        user_id: str,
        message: str,
        session_id: Optional[str] = None,
        canvas_token: Optional[str] = None,
        canvas_base_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send a message to the chatbot.

        Args:
            user_id: User ID
            message: User's message
            session_id: Optional session ID
            canvas_token: Optional Canvas API token
            canvas_base_url: Optional Canvas base URL

        Returns:
            Dict with session_id, message, tools_available, metadata

        Raises:
            ValueError: If session not found or invalid input
        """
        return await self.agent_service.chat(
            user_id=user_id,
            message=message,
            session_id=session_id,
            canvas_token=canvas_token,
            canvas_base_url=canvas_base_url,
        )

    async def get_user_sessions(
        self, user_id: str, limit: int = 20, active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Get chat sessions for a user.

        Args:
            user_id: User ID
            limit: Maximum sessions to return
            active_only: Only return active sessions

        Returns:
            List of session summaries
        """
        return await self.agent_service.get_user_sessions(
            user_id=user_id,
            limit=limit,
            active_only=active_only,
        )

    async def get_session_history(
        self, session_id: str, user_id: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get message history for a session.

        Args:
            session_id: Session ID
            user_id: User ID (for authorization)
            limit: Maximum messages to return

        Returns:
            List of messages

        Raises:
            ValueError: If session not found or unauthorized
        """
        return await self.agent_service.get_session_history(
            session_id=session_id,
            user_id=user_id,
            limit=limit,
        )

    async def delete_session(self, session_id: str, user_id: str) -> bool:
        """Delete (archive) a chat session.

        Args:
            session_id: Session ID
            user_id: User ID (for authorization)

        Returns:
            True if deleted successfully

        Raises:
            ValueError: If session not found or unauthorized
        """
        return await self.agent_service.delete_session(
            session_id=session_id,
            user_id=user_id,
        )
