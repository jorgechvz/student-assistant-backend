"""Main application entry point for API routes."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.auth_route import router as auth_router
from app.api.routes.user_route import router as user_router
from app.api.routes.notion_route import router as notion_router
from app.api.routes.google_route import router as google_router
from app.api.routes.canvas_route import router as canvas_router
from app.api.routes.chat_route import router as chat_router
from app.infrastructure.config.db import Database
from app.infrastructure.config.config import get_settings

settings = get_settings()

_logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):  # pylint: disable=unused-argument
    """Manage application lifecycle"""
    _logger.info("Starting application lifespan: connecting to database")
    await Database.connect_db(
        mongodb_uri=settings.mongodb_uri, db_name=settings.mongodb_db_name
    )
    yield
    await Database.close_db()
    _logger.info("Application lifespan ended: database connection closed")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(title="Student Assistant API", version="1.0.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    app.include_router(auth_router)
    app.include_router(user_router)
    app.include_router(notion_router)
    app.include_router(google_router)
    app.include_router(canvas_router)
    app.include_router(chat_router)

    return app


main_app = create_app()
