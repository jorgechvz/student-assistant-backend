# Setup Guide

## Prerequisites

- **Python** 3.11 – 3.13
- **Poetry** 2.x (dependency management)
- **MongoDB** 6.x+ (local or Atlas)
- **Azure OpenAI** resource with a GPT-4o deployment
- **Canvas LMS** personal access token (from your institution)
- **Google Cloud** project with Calendar API enabled (OAuth 2.0 credentials)
- **Notion** integration (created at https://www.notion.so/my-integrations)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/jorgechvz/student-assistant-backend.git
cd student-assistant-backend
```

### 2. Install Dependencies

```bash
poetry install
```

### 3. Activate the Virtual Environment

```bash
poetry shell
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```env
# ── Application ──
APP_NAME="Student Learning Assistant Backend"
ENV=local

# ── Azure OpenAI ──
AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com/
AZURE_OPENAI_KEY=your-api-key
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
AZURE_OPENAI_MODEL_NAME=gpt-4o
AZURE_REGION=eastus2
AZURE_LANGUAGE=en
AZURE_SPEECH_VOICE=en-US-JennyNeural

# ── MongoDB ──
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=student_assistant

# ── JWT Authentication ──
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# ── Cookie Settings ──
COOKIE_SECURE=false
COOKIE_HTTPONLY=true
COOKIE_SAMESITE=lax
COOKIE_DOMAIN=

# ── CORS ──
CORS_ORIGINS=["http://localhost:5173"]

# ── Notion OAuth ──
NOTION_CLIENT_ID=your-notion-client-id
NOTION_CLIENT_SECRET=your-notion-client-secret
NOTION_REDIRECT_URI=http://localhost:8000/api/v1/auth/notion/callback

# ── Google OAuth ──
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback

# ── Frontend URLs ──
FRONTEND_SUCCESS_URL=http://localhost:5173/settings?notion=success
FRONTEND_GOOGLE_SUCCESS_URL=http://localhost:5173/settings?google=success
```

### 5. Start the Server

```bash
cd src
uvicorn app.main:main_app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

## Integration Setup

### Canvas LMS

1. Log in to your Canvas LMS instance.
2. Go to **Account → Settings → New Access Token**.
3. Generate a token and copy it.
4. In the app, go to Settings and enter your Canvas base URL and token.

### Google Calendar

1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Create a project and enable the **Google Calendar API**.
3. Create **OAuth 2.0 Client ID** credentials (Web application type).
4. Add `http://localhost:8000/api/v1/auth/google/callback` as an authorized redirect URI.
5. Copy the Client ID and Client Secret to your `.env`.

### Notion

1. Go to [Notion Integrations](https://www.notion.so/my-integrations).
2. Create a new integration.
3. Set the redirect URI to `http://localhost:8000/api/v1/auth/notion/callback`.
4. Copy the Client ID and Client Secret to your `.env`.
5. Share the desired Notion pages with your integration.

## Project Structure

```
src/
├── app/
│   ├── main.py                    # Application entry point
│   ├── api/                       # API layer
│   │   ├── main.py                # FastAPI app factory + middleware
│   │   ├── dependencies/          # Dependency injection
│   │   └── routes/                # Endpoint definitions
│   ├── application/               # Business logic
│   │   ├── services/              # Core services
│   │   └── use_cases/             # Use case orchestration
│   ├── domain/                    # Domain models & interfaces
│   │   ├── db/models/             # Beanie document models
│   │   ├── db/repos/              # Repository interfaces
│   │   ├── ports/                 # External service ports
│   │   └── tools/                 # LangChain tool definitions
│   ├── infrastructure/            # Implementations
│   │   ├── adapters/              # External service adapters
│   │   ├── config/                # Settings & DB connection
│   │   └── db/repos/              # Repository implementations
│   ├── prompts/                   # Prompt templates
│   │   ├── prompt_builder.py      # Template loader & composer
│   │   └── templates/             # .txt prompt files
│   └── shared/                    # Cross-cutting concerns
│       ├── lib/                   # Utilities
│       └── schemas/               # Pydantic request/response models
└── test/                          # Test suite
```

## Running in Production

For production deployments:

1. Set `ENV=prod` in your environment.
2. Set `COOKIE_SECURE=true` and `COOKIE_SAMESITE=none`.
3. Configure `CORS_ORIGINS` with your frontend domain.
4. Use a proper MongoDB Atlas connection string for `MONGODB_URI`.
5. Use a strong, randomly generated `JWT_SECRET_KEY`.

```bash
uvicorn app.main:main_app --host 0.0.0.0 --port 8000 --workers 4
```
