"""Chat dependencies for FastAPI routes."""

from typing import Annotated
from fastapi import Depends
from app.application.use_cases.chat_uc import ChatUseCase
from app.application.use_cases.canvas_uc import CanvasUseCase
from app.application.services.agent_service import AgentService
from app.application.services.google_service import GoogleService
from app.application.services.notion_service import NotionService
from app.infrastructure.adapters.azure.aoai_adapter import AzureOpenAIAdapter
from app.infrastructure.adapters.resources.google_repo import GoogleTokenRepo
from app.infrastructure.adapters.resources.notion_repo import NotionTokenRepo
from app.infrastructure.config.config import get_settings


def get_azure_openai_adapter() -> AzureOpenAIAdapter:
    """Get Azure OpenAI Adapter instance."""
    settings = get_settings()
    return AzureOpenAIAdapter(
        azure_endpoint=settings.azure_openai_endpoint,
        azure_deployment=settings.azure_openai_deployment,
        api_key=settings.azure_openai_key,
        api_version=settings.azure_openai_api_version,
        default_temperature=0.7,
        default_max_tokens=2500,
    )


def get_google_token_repo() -> GoogleTokenRepo:
    """Get Google Token Repository instance."""
    return GoogleTokenRepo()


def get_notion_token_repo() -> NotionTokenRepo:
    """Get Notion Token Repository instance."""
    return NotionTokenRepo()


def get_google_service(
    google_token_repo: Annotated[GoogleTokenRepo, Depends(get_google_token_repo)],
) -> GoogleService:
    """Get Google Service instance."""
    return GoogleService(google_token_repo)


def get_notion_service(
    notion_token_repo: Annotated[NotionTokenRepo, Depends(get_notion_token_repo)],
) -> NotionService:
    """Get Notion Service instance."""
    return NotionService(notion_token_repo)


def get_agent_service(
    azure_openai: Annotated[AzureOpenAIAdapter, Depends(get_azure_openai_adapter)],
    google_service: Annotated[GoogleService, Depends(get_google_service)],
    notion_service: Annotated[NotionService, Depends(get_notion_service)],
) -> AgentService:
    """Get Agent Service instance."""
    return AgentService(azure_openai, google_service, notion_service)


def get_chat_use_case(
    agent_service: Annotated[AgentService, Depends(get_agent_service)],
) -> ChatUseCase:
    """Get Chat Use Case instance."""
    return ChatUseCase(agent_service)


def get_canvas_use_case() -> CanvasUseCase:
    """Get Canvas Use Case instance."""
    return CanvasUseCase()
