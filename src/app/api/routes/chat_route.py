"""Chat API Routes for Student Assistant."""

import asyncio
import json
from typing import Optional
import logging
import traceback
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from langchain_core.callbacks import AsyncCallbackHandler
from pydantic import BaseModel, Field

from app.domain.db.models.user import UserModel
from app.api.dependencies.auth_dep import get_current_user
from app.api.dependencies.chat_dep import (
    get_chat_use_case,
    get_google_token_repo,
    get_notion_token_repo,
    get_azure_openai_adapter,
    get_google_service,
    get_notion_service,
)
from app.application.services.agent_service import AgentService

from app.application.use_cases.chat_uc import ChatUseCase

__logger__ = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


class StreamingCallback(AsyncCallbackHandler):
    """Callback handler for streaming LLM responses."""

    def __init__(self, queue: asyncio.Queue):
        self.queue = queue
        self.finished = False

    async def on_llm_new_token(self, token: str, **kwargs) -> None:
        """Handle new token from LLM."""
        if not self.finished:
            await self.queue.put(token)

    async def on_llm_end(
        self, *args, **kwargs  # pylint: disable=unused-argument
    ) -> None:
        """Handle end of LLM generation."""
        if not self.finished:
            self.finished = True
            await self.queue.put(None)

    async def on_llm_error(self, error: Exception, **kwargs) -> None:
        """Handle LLM error."""
        if not self.finished:
            self.finished = True
            await self.queue.put(None)


class ChatMessageRequest(BaseModel):
    """Request model for sending a chat message."""

    message: str = Field(..., min_length=1, max_length=2000, description="User message")
    session_id: Optional[str] = Field(
        None, description="Optional session ID to continue conversation"
    )
    canvas_token: Optional[str] = Field(None, description="Optional Canvas API token")
    canvas_base_url: Optional[str] = Field(None, description="Optional Canvas base URL")


class ChatMessageResponse(BaseModel):
    """Response model for chat message."""

    session_id: str
    message: str
    tools_available: int
    metadata: dict = {}


class SessionSummary(BaseModel):
    """Summary of a chat session."""

    session_id: str
    title: str
    message_count: int
    last_message_at: Optional[str]
    created_at: str


class MessageHistory(BaseModel):
    """Message in conversation history."""

    role: str
    content: str
    created_at: str
    metadata: dict = {}


@router.post("/message", response_model=ChatMessageResponse)
async def send_message(
    request: ChatMessageRequest,
    current_user: UserModel = Depends(get_current_user),
    chat_uc: ChatUseCase = Depends(get_chat_use_case),
):
    """
    Send a message to the student assistant chatbot.

    - **message**: The message to send
    - **session_id**: Optional session ID to continue a conversation
    - **canvas_token**: Optional Canvas API token for Canvas integration
    - **canvas_base_url**: Optional Canvas LMS base URL
    """
    try:
        result = await chat_uc.send_message(
            user_id=str(current_user.id),
            message=request.message,
            session_id=request.session_id,
            canvas_token=request.canvas_token,
            canvas_base_url=request.canvas_base_url,
        )

        return ChatMessageResponse(**result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process message",
        ) from e


@router.post("/message/stream")
async def send_message_stream(
    request: ChatMessageRequest,
    current_user: UserModel = Depends(get_current_user),
):
    """Stream a message response from the student assistant chatbot."""

    async def event_generator():
        queue = asyncio.Queue()
        callback = StreamingCallback(queue)

        azure_openai = get_azure_openai_adapter()
        google_service = get_google_service(google_token_repo=get_google_token_repo())
        notion_service = get_notion_service(notion_token_repo=get_notion_token_repo())
        agent_service = AgentService(azure_openai, google_service, notion_service)

        session_id = await agent_service.get_or_create_session(
            user_id=str(current_user.id),
            session_id=request.session_id,
        )

        yield f"data: {json.dumps({'session_id': session_id, 'type': 'metadata'})}\n\n"

        task = asyncio.create_task(
            generate_with_streaming(
                request,
                current_user,
                callback,
                session_id,
            )
        )

        try:
            while True:
                token = await queue.get()
                if token is None:
                    break
                yield f"data: {json.dumps({'token': token, 'type': 'token'})}\n\n"

            await task

            yield f"data: {json.dumps({'done': True, 'session_id': session_id, 'type': 'done'})}\n\n"

        except (ValueError, RuntimeError) as e:
            yield f"data: {json.dumps({'error': str(e), 'type': 'error'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


async def generate_with_streaming(
    request: ChatMessageRequest,
    current_user: UserModel,
    callback: StreamingCallback,
    session_id: str,
):
    """Generate streaming response for chat message."""
    azure_openai = get_azure_openai_adapter()
    google_service = get_google_service(google_token_repo=get_google_token_repo())
    notion_service = get_notion_service(notion_token_repo=get_notion_token_repo())
    agent_service = AgentService(azure_openai, google_service, notion_service)

    await agent_service.chat_stream(
        user_id=str(current_user.id),
        message=request.message,
        session_id=session_id,
        canvas_token=request.canvas_token,
        canvas_base_url=request.canvas_base_url,
        callback=callback,
    )


@router.get("/sessions", response_model=list[SessionSummary])
async def list_sessions(
    limit: int = 20,
    active_only: bool = True,
    current_user: UserModel = Depends(get_current_user),
    chat_uc: ChatUseCase = Depends(get_chat_use_case),
):
    """
    Get list of chat sessions for the current user.

    - **limit**: Maximum number of sessions to return (default: 20)
    - **active_only**: Only return active sessions (default: true)
    """
    try:
        sessions = await chat_uc.get_user_sessions(
            user_id=str(current_user.id),
            limit=limit,
            active_only=active_only,
        )
        return [SessionSummary(**session) for session in sessions]

    except Exception as e:
        __logger__.error("Failed to retrieve sessions: %s", traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sessions",
        ) from e


@router.get("/sessions/{session_id}/history", response_model=list[MessageHistory])
async def get_session_history(
    session_id: str,
    limit: int = 100,
    current_user: UserModel = Depends(get_current_user),
    chat_uc: ChatUseCase = Depends(get_chat_use_case),
):
    """
    Get message history for a specific chat session.

    - **session_id**: The session ID
    - **limit**: Maximum number of messages to return (default: 100)
    """
    try:
        messages = await chat_uc.get_session_history(
            session_id=session_id,
            user_id=str(current_user.id),
            limit=limit,
        )
        return [MessageHistory(**msg) for msg in messages]

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        ) from e

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve history",
        ) from e


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user: UserModel = Depends(get_current_user),
    chat_uc: ChatUseCase = Depends(get_chat_use_case),
):
    """
    Delete (archive) a chat session.

    - **session_id**: The session ID to delete
    """
    try:
        await chat_uc.delete_session(
            session_id=session_id,
            user_id=str(current_user.id),
        )

        return {"message": "Session deleted successfully"}

    except ValueError as e:
        __logger__.error("Failed to delete session: %s", traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete session",
        ) from e
