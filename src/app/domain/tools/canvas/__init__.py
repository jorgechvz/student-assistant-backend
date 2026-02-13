"""Canvas LMS tools package."""

from .base import CanvasToolsHelper
from .core_tools import create_core_tools
from .assignment_tools import create_assignment_tools
from .grade_tools import create_grade_tools
from .analysis_tools import create_analysis_tools


def create_canvas_tools(canvas_repo, google_calendar_helper=None) -> list:
    """Create all Canvas LMS tools for LangChain agent."""
    helper = CanvasToolsHelper(canvas_repo)

    tools = []
    tools.extend(create_core_tools(helper, canvas_repo))
    tools.extend(create_assignment_tools(helper))
    tools.extend(create_grade_tools(helper, canvas_repo))
    tools.extend(
        create_analysis_tools(
            helper, canvas_repo, google_calendar_helper=google_calendar_helper
        )
    )

    return tools


__all__ = ["create_canvas_tools"]
