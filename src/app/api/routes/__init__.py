"""Routes package"""

from .auth_route import router as auth_router
from .notion_route import router as notion_router
from .google_route import router as google_router

__all__ = ["auth_router", "notion_router", "google_router"]
