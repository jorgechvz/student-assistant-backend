"""Notion dependencies for FastAPI routes"""

from typing import Annotated
from fastapi import Depends
from app.application.services.notion_service import NotionService
from app.infrastructure.adapters.resources.notion_repo import NotionTokenRepo


def get_notion_token_repo() -> NotionTokenRepo:
    """Get Notion Token Repository instance"""
    return NotionTokenRepo()


def get_notion_service(
    notion_token_repo: Annotated[NotionTokenRepo, Depends(get_notion_token_repo)],
) -> NotionService:
    """Get Notion Service instance"""
    return NotionService(notion_token_repo)
