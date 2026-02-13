# ADR-008: Dynamic Tool Resolution Per User

## Status

Accepted

## Context

Different users have different integrations connected. One user might have Canvas + Google Calendar, another might have only Notion, and a third might have nothing connected yet.

The agent needs to operate with **only the tools that the current user has access to**. Providing tools for disconnected services would:
- Cause errors when the agent tries to call them.
- Waste context window space with irrelevant tool descriptions.
- Confuse the model about available capabilities.

## Decision

We implemented **dynamic tool resolution** in `AgentService.get_user_tools()`:

1. For each integration, check if the user has a valid token in MongoDB.
2. If a token exists, create the authenticated service instance and generate the tools.
3. Return only the tools for connected integrations.

```
get_user_tools(user_id)
├── Check CanvasTokenModel → create_canvas_tools(repo)
├── Check GoogleTokenModel → create_google_calendar_tools(service, user_id)
└── Check NotionTokenModel → create_notion_tools(adapter)
→ Return combined tool list
```

The system prompt is also dynamically adjusted:
- If tools exist → load `student_assistant_system.txt` with tool instructions.
- If no tools exist → load `no_integrations_system.txt` with connection suggestions.
- For each missing integration, append a specific "connect this service" message.

## Consequences

### Positive
- The model only sees tools it can actually use, improving decision accuracy.
- Users with no integrations get a helpful prompt guiding them to connect services.
- Users with partial integrations get specific suggestions for missing services.
- No wasted tokens on irrelevant tool descriptions.
- Graceful degradation — the assistant remains functional even with zero integrations.

### Negative
- Tool resolution runs on every chat request (DB queries per integration).
- Token validation is existence-based, not freshness-based — an expired token will still load tools (errors handled at call time).
- The dynamic prompt composition adds complexity to `_get_default_system_prompt()`.
