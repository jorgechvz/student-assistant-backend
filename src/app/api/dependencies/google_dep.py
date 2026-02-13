"""Google dependencies for FastAPI routes"""

from typing import Annotated
from fastapi import Depends
from app.application.services.google_service import GoogleService
from app.infrastructure.adapters.resources.google_repo import GoogleTokenRepo


def get_google_token_repo() -> GoogleTokenRepo:
    """Get Google Token Repository instance"""
    return GoogleTokenRepo()


def get_google_service(
    google_token_repo: Annotated[GoogleTokenRepo, Depends(get_google_token_repo)],
) -> GoogleService:
    """Get Google Service instance"""
    return GoogleService(google_token_repo)
