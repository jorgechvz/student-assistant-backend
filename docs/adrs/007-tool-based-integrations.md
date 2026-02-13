# ADR-007: LangChain Tool-Based Integration Pattern

## Status

Accepted

## Context

The assistant needs to interact with three external services (Canvas LMS, Google Calendar, Notion) on behalf of the user. Each service provides multiple operations (e.g., Canvas has courses, assignments, grades, syllabus, announcements).

We needed a pattern that:
- Allows the AI model to decide when and which service operations to invoke.
- Provides clear descriptions so the model understands each tool's purpose.
- Supports adding new tools without modifying agent logic.
- Handles authentication per-user (each user has their own tokens).

## Decision

We use **LangChain's `@tool` decorator** with a **factory function pattern**:

```python
def create_canvas_tools(canvas_repo: CanvasRepository) -> list:
    @tool
    def get_current_courses() -> str:
        """Get all currently enrolled courses. Use when the student asks
        about their courses, classes, or enrolled subjects."""
        return canvas_repo.get_courses()
    
    return [get_current_courses, ...]
```

Key design choices:
- **Factory functions** (`create_canvas_tools`, `create_google_calendar_tools`, `create_notion_tools`) create tool closures that capture authenticated service instances.
- **Rich docstrings** serve as the model's tool descriptions — they follow a "Use when..." pattern to guide the model's tool selection.
- Tools are organized by integration in separate modules under `domain/tools/`.
- Canvas tools are further split into sub-modules (`core_tools`, `assignment_tools`, `grade_tools`, `analysis_tools`).

## Consequences

### Positive
- The AI model autonomously decides which tools to invoke based on user intent — no hardcoded routing.
- Adding a new tool is a single function with a `@tool` decorator and descriptive docstring.
- Factory pattern ensures each user gets tools bound to their authenticated sessions.
- Tool descriptions follow a consistent "Use when..." pattern, improving model accuracy.
- Tool organization by integration keeps modules focused.

### Negative
- Tool descriptions require careful wording — vague descriptions lead to incorrect tool selection.
- Too many tools can overwhelm the model's context window and degrade decision quality.
- Error handling in tools must be robust — unhandled exceptions can break the agent loop.
- Testing tools requires mocking the captured service instances.
