# Architecture Overview

## System Architecture

Loop (Student Learning Assistant) follows a **layered architecture** inspired by Clean Architecture / Hexagonal Architecture principles. The system is organized into concentric layers with clear dependency rules: outer layers depend on inner layers, never the reverse.

```
┌─────────────────────────────────────────────────────────────────-┐
│                        API Layer (FastAPI)                       │
│   Routes · Dependencies · Request/Response Schemas · SSE         │
├─────────────────────────────────────────────────────────────────-┤
│                      Application Layer                           │
│   Use Cases · Services · Agent Orchestration · Prompt Builder    │
├─────────────────────────────────────────────────────────────────-┤
│                        Domain Layer                              │
│   Models · Repository Interfaces · Ports · Tool Definitions      │
├─────────────────────────────────────────────────────────────────-┤
│                     Infrastructure Layer                         │
│   Adapters · Database · External APIs · Security                 │
└─────────────────────────────────────────────────────────────────-┘
```

## High-Level Component Diagram

```
                        ┌──────────────────┐
                        │   Frontend (SPA) │
                        │   React / Vite   │
                        └────────┬─────────┘
                                 │ HTTPS (Cookies)
                        ┌────────▼─────────┐
                        │   FastAPI Server │
                        │   /api/v1        │
                        └────────┬─────────┘
              ┌─────────────────-┼─────────────────┐
              │                  │                 │
     ┌────────▼──────┐  ┌───────-▼──────┐  ┌───────▼───────-┐
     │  Auth Module  │  │  Chat Module  │  │ Settings Module│
     │  /auth/*      │  │  /chat/*      │  │  /user/*       │
     └────────┬──────┘  └───────┬───────┘  └───────────────-┘
              │                 │
              │          ┌──────▼-───────┐
              │          │ Agent Service │
              │          │ (Orchestrator)│
              │          └───────┬───────┘
              │     ┌────────────┼────────────------┐
              │     │            │                  │
        ┌─────▼─────▼──┐ ┌──────-▼────----┐ ┌───----▼──────-┐
        │   MongoDB    │ │ Azure OpenAI   │ │  LangChain    │
        │   (Beanie)   │ │  (GPT-4o-mini) │ │  Agent + Tools│
        └──────────────┘ └────────────----┘ └───-----┬─────-┘
                                            ┌────────┼───────-─┐
                                        ┌────▼───┐ ┌──▼──-┐ ┌───▼────┐
                                        │ Canvas │ │Google│ │ Notion │
                                        │  LMS   │ │ Cal  │ │  API   │
                                        └────────┘ └─────-┘ └────────┘
```

## Layer Descriptions

### API Layer (`src/app/api/`)

The outermost layer responsible for HTTP concerns:

- **Routes**: FastAPI routers defining endpoints, request validation, and response serialization.
- **Dependencies**: Dependency injection factories for services, repositories, and authentication.
- **Schemas**: Pydantic models for request/response contracts (separate from domain models).

| Router         | Prefix         | Responsibility                                     |
| -------------- | -------------- | -------------------------------------------------- |
| `auth_route`   | `/auth`        | Signup, login, logout, token refresh               |
| `user_route`   | `/user`        | Profile management, account settings, integrations |
| `chat_route`   | `/chat`        | Conversations, streaming SSE, session management   |
| `canvas_route` | `/canvas`      | Canvas LMS setup, connection status, assignments   |
| `google_route` | `/auth/google` | Google OAuth flow, token management                |
| `notion_route` | `/auth/notion` | Notion OAuth flow, token management                |

### Application Layer (`src/app/application/`)

Business logic orchestration:

- **Services**: Core business logic implementations (`AgentService`, `AuthService`, `GoogleService`, `NotionService`, `UserSettingsService`, `TokenService`).
- **Use Cases**: Thin orchestration layer delegating to services (e.g., `ChatUseCase`, `CanvasUseCase`).

### Domain Layer (`src/app/domain/`)

The innermost layer with zero external dependencies:

- **Models**: Beanie Document models (`UserModel`, `ChatSessionModel`, `MessageModel`, `CanvasTokenModel`, `GoogleTokenModel`, `NotionTokenModel`).
- **Repository Interfaces**: Abstract base classes defining data access contracts (e.g., `UserRepoInterface`).
- **Ports**: Interface definitions for external services (`AzureOpenAIPort`, `ResourcesPort`).
- **Tools**: LangChain `@tool` definitions for the AI agent (Canvas, Google Calendar, Notion).

### Infrastructure Layer (`src/app/infrastructure/`)

Concrete implementations of domain ports:

- **Adapters**: `AzureOpenAIAdapter`, `CanvasRepository`, `NotionAPIAdapter`, `PasswordHasher`, `JWTHandler`.
- **Config**: Application settings (`Settings` via Pydantic), database connection (`Database`).
- **DB Repos**: Beanie-based repository implementations (`UserRepoBeanie`).

### Prompts (`src/app/prompts/`)

Template-driven prompt management:

- **`PromptBuilder`**: Service that loads and composes prompt templates.
- **Templates**: `guardrails.txt` (identity + academic integrity), `student_assistant_system.txt` (tool usage instructions), `no_integrations_system.txt` (fallback when nothing is connected).

## Data Flow: Chat Message

```
1. User sends message via POST /chat/stream
2. FastAPI route validates auth (JWT cookie)
3. ChatUseCase delegates to AgentService
4. AgentService:
   a. Resolves available tools (checks Canvas/Google/Notion tokens in DB)
   b. Loads conversation history (last 20 messages)
   c. Builds dynamic system prompt via PromptBuilder
   d. Calls AzureOpenAIAdapter.astream() with LangChain agent
5. Agent may invoke tools (Canvas API, Google Calendar API, Notion API)
6. Response tokens are streamed via SSE to the frontend
7. Complete response is saved to MongoDB
```

## Authentication Flow

```
1. User signs up / logs in → AuthService validates credentials
2. TokenService creates JWT access + refresh token pair
3. Tokens set as httponly cookies (secure, SameSite)
4. Every request: get_current_user dependency extracts + verifies access_token cookie
5. On expiry: frontend calls /auth/refresh with refresh_token cookie
```

## Integration OAuth Flows

```
Google Calendar:
  GET /auth/google/authorize → Redirect to Google consent screen
  GET /auth/google/callback  → Exchange code → Store tokens → Redirect to frontend

Notion:
  GET /auth/notion/authorize → Redirect to Notion consent screen
  GET /auth/notion/callback  → Exchange code → Store tokens → Redirect to frontend

Canvas LMS:
  POST /canvas/setup → Validate token against Canvas API → Store in DB
  (Canvas uses personal access tokens, not OAuth)
```

## Database Schema

```
MongoDB Collections:
├── users              → UserModel (email, password_hash, full_name, is_active)
├── canvas_tokens      → CanvasTokenModel (user_id, access_token, canvas_base_url)
├── google_tokens      → GoogleTokenModel (user_id, access_token, refresh_token, expires_at)
├── notion_tokens      → NotionTokenModel (user_id, access_token, workspace_id)
├── chat_sessions      → ChatSessionModel (user_id, title, is_active, created_at)
└── messages           → MessageModel (session_id, user_id, role, content, tool_calls)
```

## Technology Stack

| Component         | Technology               | Purpose                                               |
| ----------------- | ------------------------ | ----------------------------------------------------- |
| Web Framework     | FastAPI                  | Async HTTP server, dependency injection, OpenAPI docs |
| AI/LLM            | Azure OpenAI (GPT-4o-mini)    | Language model for the assistant                      |
| Agent Framework   | LangChain                | Tool-calling agent orchestration                      |
| Database          | MongoDB + Motor          | Async document storage                                |
| ODM               | Beanie                   | Document-model mapping for MongoDB                    |
| Auth              | PyJWT + bcrypt           | JWT tokens + password hashing                         |
| Streaming         | Server-Sent Events (SSE) | Real-time token-by-token response delivery            |
| Config            | Pydantic Settings        | Type-safe environment configuration                   |
| Canvas LMS        | REST API                 | Course data, assignments, grades                      |
| Google Calendar   | Google Calendar API v3   | Event management, scheduling                          |
| Notion            | Notion API               | Note-taking, study materials                          |
| Markdown → Notion | mistletoe                | Markdown parsing to Notion blocks                     |
