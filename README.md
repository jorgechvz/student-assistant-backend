# Loop — Student Learning Assistant

> An AI-powered chatbot that helps students manage their academic experience across courses, calendars, and notes without doing the work for them.

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.128-009688?logo=fastapi)
![LangChain](https://img.shields.io/badge/LangChain-Agent-orange)
![Azure OpenAI](https://img.shields.io/badge/Azure_OpenAI-GPT--4o-0078D4?logo=microsoftazure)
![MongoDB](https://img.shields.io/badge/MongoDB-Beanie-47A248?logo=mongodb)

---

## What is Loop?

Loop is an AI student assistant that connects to the tools students already use — **Canvas LMS**, **Google Calendar**, and **Notion** to provide a unified, intelligent interface for academic management.

Students can ask questions like:
- *"What assignments are due this week?"*
- *"Schedule study sessions for my upcoming exam"*
- *"Create study notes for Chapter 5 in Notion"*
- *"How am I doing in CS 101?"*

Loop focuses on **organization, planning, and understanding** never on completing work for students. Academic integrity guardrails ensure the assistant supports learning without enabling cheating.

---

## Features

### AI Chat Assistant
- Natural language conversations powered by Azure OpenAI (GPT-4o-mini)
- Real-time streaming responses via Server-Sent Events (SSE)
- Context-aware, remembers your courses and prior conversation
- Responds in the student's language (multi-language support)

### Canvas LMS Integration
- View enrolled courses, assignments, grades, and syllabus
- Query upcoming, past, overdue, and unsubmitted assignments
- Access course announcements and materials
- Flexible course matching (name, code, or ID)

###  Google Calendar Integration
- Create assignment reminders with automatic notifications (24h + 1h)
- Generate personalized study plans based on workload and deadlines
- Check availability and schedule study sessions
- Timezone-aware scheduling (auto-detects from Google settings)

###  Notion Integration
- Create structured study notes with proper formatting
- Build assignment trackers with status and due dates
- Generate organized study plan pages
- Search existing Notion pages and databases

###  Academic Integrity
- Refuses to solve homework, write essays, or provide exam answers
- Redirects students to study strategies and tool-based alternatives
- Validated against 15 predefined misuse test scenarios
- Prompt-level guardrails loaded from template files

###  User Settings
- Update profile (name, email)
- Change password
- View and manage connected integrations
- Delete account with full data cascade

---

##  Architecture

Loop follows a **layered architecture** inspired by Clean Architecture:

```
┌──────────────────────────────────────────┐
│           API Layer (FastAPI)             │
├──────────────────────────────────────────┤
│        Application Layer (Services)       │
├──────────────────────────────────────────┤
│      Domain Layer (Models & Ports)        │
├──────────────────────────────────────────┤
│   Infrastructure Layer (Adapters & DB)    │
└──────────────────────────────────────────┘
```

**Key components:**
- **AgentService** — Orchestrates the LangChain agent with dynamic tool resolution
- **PromptBuilder** — Composes system prompts from template files
- **Dynamic Tool Resolution** — Only loads tools for integrations the user has connected
- **SSE Streaming** — Token-by-token response delivery for real-time chat UX

See [docs/architecture.md](docs/architecture.md) for full diagrams and details.

---

##  Quick Start

### Prerequisites

- Python 3.11 – 3.13
- [Poetry](https://python-poetry.org/) 2.x
- MongoDB 6.x+ (or [MongoDB Atlas](https://www.mongodb.com/atlas))
- [Azure OpenAI](https://azure.microsoft.com/en-us/products/ai-services/openai-service/) resource

### Installation

```bash
# Clone the repository
git clone https://github.com/jorgechvz/student-assistant-backend.git
cd student-assistant-backend

# Install dependencies
poetry install

# Configure environment
cp .env.example .env  # Edit with your credentials

# Start the server
cd src
uvicorn app.main:main_app --reload --port 8000
```

API available at `http://localhost:8000` · Docs at `http://localhost:8000/docs`

See [docs/setup-guide.md](docs/setup-guide.md) for complete setup instructions including integration configuration.

---

##  API Endpoints

| Module | Method | Endpoint | Description |
|--------|--------|----------|-------------|
| **Auth** | `POST` | `/auth/signup` | Register new account |
| | `POST` | `/auth/login` | Login |
| | `POST` | `/auth/logout` | Logout (clear cookies) |
| | `POST` | `/auth/refresh` | Refresh access token |
| | `GET` | `/auth/me` | Get current user |
| **Chat** | `POST` | `/chat` | Send message (non-streaming) |
| | `POST` | `/chat/stream` | Send message (SSE streaming) |
| | `GET` | `/chat/sessions` | List chat sessions |
| | `GET` | `/chat/sessions/{id}/messages` | Get session messages |
| | `DELETE` | `/chat/sessions/{id}` | Delete session |
| **User** | `GET` | `/user/profile` | Get profile + integration status |
| | `PATCH` | `/user/profile` | Update name/email |
| | `POST` | `/user/change-password` | Change password |
| | `DELETE` | `/user/account` | Delete account |
| | `GET` | `/user/integrations` | Integration status |
| | `DELETE` | `/user/integrations/{name}` | Disconnect integration |
| **Canvas** | `POST` | `/canvas/setup` | Connect Canvas |
| | `GET` | `/canvas/status` | Connection status |
| | `GET` | `/canvas/upcoming-assignments` | All upcoming assignments |
| | `DELETE` | `/canvas/disconnect` | Disconnect Canvas |
| **Google** | `GET` | `/auth/google/authorize` | Start OAuth flow |
| | `GET` | `/auth/google/callback` | OAuth callback |
| | `GET` | `/auth/google/status` | Connection status |
| | `DELETE` | `/auth/google/disconnect` | Disconnect Google |
| **Notion** | `GET` | `/auth/notion/authorize` | Start OAuth flow |
| | `GET` | `/auth/notion/callback` | OAuth callback |
| | `GET` | `/auth/notion/status` | Connection status |
| | `DELETE` | `/auth/notion/disconnect` | Disconnect Notion |

See [docs/api-reference.md](docs/api-reference.md) for full request/response documentation.

---

##  Project Structure

```
src/app/
├── api/                    # FastAPI routes & dependencies
│   ├── routes/             # Endpoint definitions
│   └── dependencies/       # Dependency injection
├── application/            # Business logic
│   ├── services/           # Core services (Agent, Auth, Google, Notion, etc.)
│   └── use_cases/          # Use case orchestration
├── domain/                 # Core models & interfaces
│   ├── db/models/          # Beanie document models
│   ├── db/repos/           # Repository interfaces
│   ├── ports/              # External service ports
│   └── tools/              # LangChain tool definitions
│       └── canvas/         # Canvas tools (core, assignments, grades, analysis)
├── infrastructure/         # Implementations
│   ├── adapters/           # Azure, Canvas, Notion, Security adapters
│   ├── config/             # Settings & DB connection
│   └── db/repos/           # Repository implementations
├── prompts/                # AI prompt management
│   ├── prompt_builder.py   # Template loader
│   └── templates/          # guardrails.txt, system prompts
└── shared/                 # Schemas & utilities
```

---

##  Technology Stack

| Layer | Technology |
|-------|-----------|
| Web Framework | FastAPI (async, OpenAPI auto-docs) |
| AI / LLM | Azure OpenAI GPT-4o |
| Agent Framework | LangChain (tool-calling agent) |
| Database | MongoDB + Motor (async) + Beanie (ODM) |
| Authentication | PyJWT + bcrypt (httponly cookies) |
| Streaming | Server-Sent Events (SSE) |
| Canvas LMS | REST API (personal access tokens) |
| Google Calendar | Google Calendar API v3 (OAuth 2.0) |
| Notion | Notion API (OAuth 2.0) |
| Markdown Parser | mistletoe (Markdown → Notion blocks) |
| Config | Pydantic Settings (.env) |
| Package Manager | Poetry |

---

##  Documentation

| Document | Description |
|----------|-------------|
| [Architecture](docs/architecture.md) | System architecture, diagrams, data flows |
| [API Reference](docs/api-reference.md) | Complete endpoint documentation |
| [Setup Guide](docs/setup-guide.md) | Installation and configuration |
| [Requirements](docs/requirements.md) | Project scope, goals, constraints |
| [Academic Integrity](docs/academic-integrity.md) | Guardrails and misuse prevention |
| [Evaluation Plan](docs/evaluation-plan.md) | Test cases and benchmarks |
| [Project Artifacts](docs/artifacts.md) | Deliverable artifact catalog |
| [ADRs](docs/adrs/README.md) | Architecture Decision Records (10 ADRs) |

---

##  Author

**Jorge Chavez** — [jchavezponce@byupathway.edu](mailto:jchavezponce@byupathway.edu)

---

## Frontend

The React frontend application lives in a separate repository:

- **Repository:** [student-assistant-frontend](https://github.com/jorgechvz/student-assistant-frontend)
- **Tech Stack:** React 19, TypeScript, Vite, Tailwind CSS v4, Radix UI, Zustand, TanStack Query
- **Deployment:** Vercel

The backend is deployed on **Render**.

---

##  License

This project was developed as a capstone project for academic purposes.