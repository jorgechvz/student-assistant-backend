"""Agent Service for Student Assistant Chatbot orchestration."""

import logging

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from beanie import PydanticObjectId
from app.domain.db.models.chat import ChatSessionModel, MessageModel
from app.domain.tools.canvas import create_canvas_tools
from app.domain.tools.google_calendar_tools import create_google_calendar_tools
from app.domain.tools.notion_tools import create_notion_tools
from app.infrastructure.adapters.azure.aoai_adapter import AzureOpenAIAdapter
from app.infrastructure.adapters.resources.canvas_repo import CanvasRepository
from app.infrastructure.adapters.resources.notion_api_adapter import NotionAPIAdapter
from app.application.services.google_service import GoogleService
from app.application.services.notion_service import NotionService
from app.domain.db.models.canvas import CanvasTokenModel
from app.domain.tools.google_calendar_tools import GoogleCalendarHelper
from app.prompts.prompt_builder import PromptBuilder


_logger = logging.getLogger(__name__)


class AgentService:
    """Service for orchestrating the student assistant agent."""

    def __init__(
        self,
        azure_openai_adapter: AzureOpenAIAdapter,
        google_service: GoogleService,
        notion_service: NotionService,
    ):
        """Initialize Agent Service.

        Args:
            azure_openai_adapter: Azure OpenAI adapter instance
            google_service: Google OAuth service
            notion_service: Notion OAuth service
        """
        self.azure_openai = azure_openai_adapter
        self.google_service = google_service
        self.notion_service = notion_service

    async def get_user_tools(
        self,
        user_id: str,
        canvas_token: Optional[str] = None,
        canvas_base_url: Optional[str] = None,
    ) -> List[Any]:
        """Get available tools for a user based on their connected integrations.

        Args:
            user_id: User ID
            canvas_token: Optional Canvas API token (overrides DB token)
            canvas_base_url: Optional Canvas LMS base URL (overrides DB URL)

        Returns:
            List of LangChain tools available to the user
        """
        tools = []

        if not canvas_token or not canvas_base_url:
            try:

                canvas_token_model = await CanvasTokenModel.find_one(
                    CanvasTokenModel.user_id == user_id
                )
                if canvas_token_model:
                    canvas_token = canvas_token_model.access_token
                    canvas_base_url = canvas_token_model.canvas_base_url
            except (AttributeError, TypeError) as e:
                _logger.debug("No Canvas token in DB: %s", e)

        if canvas_token and canvas_base_url:
            try:
                canvas_repo = CanvasRepository(canvas_base_url, canvas_token)
                canvas_tools = create_canvas_tools(canvas_repo)
                tools.extend(canvas_tools)
                _logger.info("Canvas tools loaded for user %s", user_id)
            except (AttributeError, TypeError) as e:
                _logger.warning("Failed to load Canvas tools: %s", e)

        try:
            google_token = await self.google_service.get_user_token(user_id)
            if google_token:
                google_tools = create_google_calendar_tools(
                    self.google_service, user_id
                )
                tools.extend(google_tools)
                _logger.info("Google Calendar tools loaded for user %s", user_id)
        except (AttributeError, TypeError) as e:
            _logger.warning("Failed to load Google Calendar tools: %s", e)

        try:
            notion_token = await self.notion_service.get_user_token(user_id)
            if notion_token:
                notion_adapter = NotionAPIAdapter(notion_token.access_token)

                notion_adapter.get_current_date = lambda: datetime.now(
                    timezone.utc
                ).strftime("%Y-%m-%d")

                notion_tools = create_notion_tools(notion_adapter)
                tools.extend(notion_tools)
                _logger.info("Notion tools loaded for user %s", user_id)
        except (AttributeError, TypeError) as e:
            _logger.warning("Failed to load Notion tools: %s", e)

        return tools

    async def chat(
        self,
        user_id: str,
        message: str,
        session_id: Optional[str] = None,
        canvas_token: Optional[str] = None,
        canvas_base_url: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Process a chat message with the student assistant agent.

        Args:
            user_id: User ID
            message: User's message
            session_id: Optional session ID (creates new if not provided)
            canvas_token: Optional Canvas API token
            canvas_base_url: Optional Canvas base URL
            system_prompt: Optional custom system prompt

        Returns:
            Dict with agent response and session info
        """
        if session_id:
            session = await ChatSessionModel.find_one(
                ChatSessionModel.id == PydanticObjectId(session_id),
                ChatSessionModel.user_id == user_id,
            )
            if not session:
                raise ValueError("Session not found")
        else:
            session = ChatSessionModel(
                user_id=user_id,
                title=None,
                message_count=0,
            )
            await session.save()
            session_id = str(session.id)

        history = await self._load_conversation_history(session_id, limit=20)

        user_msg = MessageModel(
            session_id=session_id,
            user_id=user_id,
            role="user",
            content=message,
        )
        await user_msg.save()

        tools = await self.get_user_tools(user_id, canvas_token, canvas_base_url)

        messages = history + [{"role": "user", "content": message}]

        if not system_prompt:
            system_prompt = self._get_default_system_prompt(tools)

        try:
            response = self.azure_openai.chat_completion(
                messages=messages, tools=tools, system_prompt=system_prompt
            )

            assistant_content = response.get("text", "")
            metadata = response.get("metadata", {})

            assistant_msg = MessageModel(
                session_id=session_id,
                user_id=user_id,
                role="assistant",
                content=assistant_content,
                metadata=metadata,
            )
            await assistant_msg.save()

            session.message_count += 2
            session.last_message_at = datetime.now(timezone.utc)

            if not session.title and session.message_count == 2:
                session.title = await self._generate_session_title(
                    message,
                    history
                    + [
                        {"role": "user", "content": message},
                        {"role": "assistant", "content": assistant_content},
                    ],
                )

            await session.save()

            return {
                "session_id": session_id,
                "message": assistant_content,
                "metadata": metadata,
                "tools_available": len(tools),
            }

        except Exception as e:
            _logger.error("Agent error: %s", e)
            raise

    async def _load_canvas_tools(self, user_id: str) -> List:
        """Load Canvas LMS integration tools."""
        canvas_repo = await self._get_canvas_repo(user_id)
        if not canvas_repo:
            return []

        google_helper = None
        try:
            google_service = self._get_google_service()

            google_helper = GoogleCalendarHelper(google_service, user_id)
        except Exception:
            pass

        tools = create_canvas_tools(canvas_repo, google_calendar_helper=google_helper)
        _logger.info("Canvas tools loaded for user %s", user_id)
        return tools

    async def _load_conversation_history(
        self, session_id: str, limit: int = 20
    ) -> List[Dict[str, str]]:
        """Load conversation history for a session.

        Args:
            session_id: Session ID
            limit: Maximum number of messages to load

        Returns:
            List of message dicts
        """
        messages = (
            await MessageModel.find(MessageModel.session_id == session_id)
            .sort("-created_at")
            .limit(limit)
            .to_list()
        )

        messages.reverse()

        return [{"role": msg.role, "content": msg.content} for msg in messages]

    def _get_default_system_prompt(self, tools: List[Any]) -> str:
        """Generate default system prompt from template files.

        Combines: guardrails (personality + rules) + tool instructions +
        integration connection suggestions for missing services.
        """
        prompt_builder = PromptBuilder()
        tool_names = {getattr(t, "name", "") for t in tools}

        has_canvas = any("course" in n or "assignment" in n or "syllabus" in n or "grade" in n for n in tool_names)
        has_google = any("calendar" in n or "event" in n or "schedule" in n or "timezone" in n for n in tool_names)
        has_notion = any("notion" in n for n in tool_names)
        has_any = has_canvas or has_google or has_notion

        parts = [prompt_builder.guardrails_prompt()]

        if has_any:
            parts.append(prompt_builder.student_assistant_system_prompt(has_integrations=True))

        missing = []
        if not has_canvas:
            missing.append(
                "- **Canvas LMS** is NOT connected. If the student asks about courses, "
                "assignments, grades, or syllabus, tell them: "
                '"You need to connect Canvas first! Go to Settings in the app and add your Canvas API token."'
            )
        if not has_google:
            missing.append(
                "- **Google Calendar** is NOT connected. If the student asks about "
                "scheduling, events, or their calendar, tell them: "
                '"Connect your Google account in Settings to manage your calendar!"'
            )
        if not has_notion:
            missing.append(
                "- **Notion** is NOT connected. If the student asks about notes, "
                "study plans, or saving content to Notion, tell them: "
                '"Connect your Notion workspace in Settings to start organizing!"'
            )

        if missing:
            parts.append(
                "INTEGRATION STATUS — Some services are not connected:\n"
                + "\n".join(missing)
                + "\n\nAlways suggest the student go to Settings to connect the missing services."
            )

        if not has_any:
            parts.append(prompt_builder.student_assistant_system_prompt(has_integrations=False))

        return "\n\n".join(parts)

    async def _generate_session_title(
        self,
        first_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """Generate a session title using AI based on the first message and optional conversation history.

        Args:
            first_message: First message in the session
            conversation_history: Optional conversation history for more context

        Returns:
            Session title (max 60 characters)
        """
        try:
            context = f"User's first message: {first_message}"

            if conversation_history and len(conversation_history) > 1:
                assistant_response = next(
                    (
                        msg["content"]
                        for msg in conversation_history
                        if msg["role"] == "assistant"
                    ),
                    None,
                )
                if assistant_response:
                    context += f"\nAssistant's response: {assistant_response[:200]}"

            title_prompt = """Generate a short, descriptive title (maximum 40 characters) for this conversation.
                The title should capture the main topic or intent.
                Only return the title text, nothing else.

                Examples:
                - "Canvas Course Overview"
                - "Assignment Due Dates"
                - "Study Plan for Midterms"
                - "Google Calendar Integration"
                - "Notion Study Notes"

                Context:
                """
            messages = [{"role": "user", "content": title_prompt + context}]

            response = self.azure_openai.chat_completion(
                messages=messages,
                system_prompt="You are a helpful assistant that generates concise, descriptive titles for student conversations.",
                temperature=0.7,
                max_tokens=15,
            )

            title = response.get("text", "").strip()

            title = title.strip("\"'")

            if len(title) > 60:
                title = title[:57] + "..."

            if not title or len(title) < 5:
                raise ValueError("AI generated title too short")

            _logger.info("Generated AI title: %s", title)
            return title

        except (AttributeError, ValueError) as e:
            _logger.warning("Failed to generate AI title, using fallback: %s", e)
            title = first_message[:57].strip()
            if len(first_message) > 57:
                title += "..."
            return title

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
        if active_only:
            sessions = (
                await ChatSessionModel.find(
                    ChatSessionModel.user_id == user_id,
                    ChatSessionModel.is_active == True,
                )
                .sort("-last_message_at")
                .limit(limit)
                .to_list()
            )
        else:
            sessions = (
                await ChatSessionModel.find(
                    ChatSessionModel.user_id == user_id,
                )
                .sort("-last_message_at")
                .limit(limit)
                .to_list()
            )

        return [
            {
                "session_id": str(session.id),
                "title": session.title or "New conversation",
                "message_count": session.message_count,
                "last_message_at": (
                    session.last_message_at.isoformat()
                    if session.last_message_at
                    else None
                ),
                "created_at": session.created_at.isoformat(),
            }
            for session in sessions
        ]

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
        """
        session = await ChatSessionModel.find_one(
            ChatSessionModel.id == PydanticObjectId(session_id),
            ChatSessionModel.user_id == user_id,
        )
        if not session:
            raise ValueError("Session not found")

        messages = (
            await MessageModel.find(MessageModel.session_id == session_id)
            .sort("+created_at")
            .limit(limit)
            .to_list()
        )

        return [
            {
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at.isoformat(),
                "metadata": msg.metadata if msg.metadata is not None else {},
            }
            for msg in messages
        ]

    async def delete_session(self, session_id: str, user_id: str) -> bool:
        """Delete (archive) a chat session.
        Args:
            session_id: Session ID
            user_id: User ID (for authorization)
        Returns:
            True if deleted successfully
        """

        session = await ChatSessionModel.find_one(
            ChatSessionModel.id == PydanticObjectId(session_id),
            ChatSessionModel.user_id == user_id,
        )

        if not session:
            raise ValueError("Session not found")

        await MessageModel.find(MessageModel.session_id == session_id).delete()

        await session.delete()

        return True

    async def get_or_create_session(
        self, user_id: str, session_id: Optional[str] = None
    ) -> str:
        """Get existing session or create a new one.

        Args:
            user_id: User ID
            session_id: Optional existing session ID

        Returns:
            session_id: The session ID (existing or newly created)

        Raises:
            ValueError: If session_id provided but not found
        """
        if session_id:
            session = await ChatSessionModel.find_one(
                ChatSessionModel.id == PydanticObjectId(session_id),
                ChatSessionModel.user_id == user_id,
            )
            if not session:
                raise ValueError("Session not found")
            return session_id
        else:
            session = ChatSessionModel(
                user_id=user_id,
                title=None,
                message_count=0,
            )
            await session.save()
            return str(session.id)

    async def chat_stream(
        self,
        user_id: str,
        message: str,
        callback: Any,
        session_id: str,
        canvas_token: Optional[str] = None,
        canvas_base_url: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> None:
        """
        Process a chat message with the student assistant agent using streaming.

        Args:
            user_id: User ID
            message: User's message
            callback: Callback for streaming tokens
            session_id: Session ID
            canvas_token: Optional Canvas API token
            canvas_base_url: Optional Canvas base URL
            system_prompt: Optional custom system prompt
        Returns:
            None
        """

        session = await ChatSessionModel.find_one(
            ChatSessionModel.id == PydanticObjectId(session_id),
            ChatSessionModel.user_id == user_id,
        )
        if not session:
            raise ValueError("Session not found")

        history = await self._load_conversation_history(session_id, limit=20)

        user_msg = MessageModel(
            session_id=session_id,
            user_id=user_id,
            role="user",
            content=message,
        )
        await user_msg.save()

        tools = await self.get_user_tools(user_id, canvas_token, canvas_base_url)

        messages = history + [{"role": "user", "content": message}]

        if not system_prompt:
            system_prompt = self._get_default_system_prompt(tools)

        try:
            response = await self.azure_openai.chat_completion_stream(
                messages=messages,
                tools=tools,
                system_prompt=system_prompt,
                callback=callback,
            )

            assistant_content = response.get("text", "")
            metadata = response.get("metadata", {})

            assistant_msg = MessageModel(
                session_id=session_id,
                user_id=user_id,
                role="assistant",
                content=assistant_content,
                metadata=metadata,
            )
            await assistant_msg.save()

            session.message_count += 2
            session.last_message_at = datetime.now(timezone.utc)

            if not session.title and session.message_count == 2:
                session.title = await self._generate_session_title(
                    message,
                    history
                    + [
                        {"role": "user", "content": message},
                        {"role": "assistant", "content": assistant_content},
                    ],
                )

            await session.save()

        except Exception as e:
            _logger.error("Agent streaming error: %s", e, exc_info=True)
            raise
