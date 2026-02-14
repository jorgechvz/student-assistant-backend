# Project Artifacts

## Overview

This document catalogs all deliverable artifacts for the Student Learning Assistant (Loop) project, organized into **Process Artifacts** (documenting the development journey) and **Final Results Artifacts** (demonstrating the completed system).

---

## Process Artifacts

### 1. Project Requirements & Scope Document

Defines project goals, assumptions, constraints, and non-goals.

**Location:** [docs/requirements.md](requirements.md)

**Contents:**

- Project summary and goals
- Assumptions and constraints
- Explicit non-goals
- Measurable objectives with targets
- Stakeholder roles
- Integration map

---

### 2. System Architecture & Integration Diagrams

Visual diagrams showing how the assistant integrates with the course platform, calendar, and note-taking tools.

**Location:** [docs/architecture.md](architecture.md)

**Contents:**

- High-level component diagram
- Layered architecture breakdown (API → Application → Domain → Infrastructure)
- Data flow diagrams (chat message lifecycle, authentication flow, OAuth flows)
- Database schema (6 MongoDB collections)
- Technology stack table

---

### 3. Academic Integrity & Misuse Prevention Guidelines

Documentation describing guardrails, restricted behaviors, and misuse test cases.

**Location:** [docs/academic-integrity.md](academic-integrity.md)

**Contents:**

- 5 core non-negotiable principles
- Guardrails implementation (prompt-based, template-driven)
- Redirection strategy (Acknowledge → Redirect → Offer Alternatives)
- Restricted behavior matrix (homework, essays, exams, quizzes, code)
- Scope boundaries (what the assistant will and won't engage with)
- 15 predefined misuse test scenarios with expected behaviors

---

### 4. Evaluation Plan & Test Cases

A set of predefined questions and scenarios used to measure assistant accuracy, safety, and performance.

**Location:** [docs/evaluation-plan.md](evaluation-plan.md)

**Contents:**

- 31 functional test cases across 5 categories:
  - Course information retrieval (7 tests)
  - Calendar & study planning (7 tests)
  - Notion integration (5 tests)
  - Integration reliability (7 tests)
  - Conversation quality (5 tests)
- Safety validation criteria (linked to misuse prevention)
- Performance benchmarks (latency, throughput, memory)
- Scoring methodology

---

### 5. Architecture Decision Records (ADRs)

Documentation of significant architectural decisions with context, rationale, and consequences.

**Location:** [docs/adrs/](adrs/README.md)

**Records:**
| ADR | Decision |
|-----|----------|
| ADR-001 | Layered Architecture with Clean Architecture Principles |
| ADR-002 | Azure OpenAI with LangChain Agent Framework |
| ADR-003 | MongoDB with Beanie ODM |
| ADR-004 | JWT Authentication with HttpOnly Cookies |
| ADR-005 | Server-Sent Events for Chat Streaming |
| ADR-006 | Template-Based Prompt Management |
| ADR-007 | LangChain Tool-Based Integration Pattern |
| ADR-008 | Dynamic Tool Resolution Per User |
| ADR-009 | Canvas LMS Personal Access Tokens vs OAuth |
| ADR-010 | Prompt-Level Academic Integrity Guardrails |

---

## Final Results Artifacts

### 1. Working Prototype of the Student Learning Assistant

A functional chatbot demonstrating course queries, reminders, study planning, and summaries.

**Capabilities Demonstrated:**

- Natural language queries about courses, assignments, grades, and deadlines
- Automated study session scheduling in Google Calendar
- Structured study note creation in Notion
- Real-time streaming responses via SSE
- Multi-language support (responds in the student's language)
- Academic integrity enforcement with helpful redirection

**Access:** Run the backend server and connect via the React frontend application.

---

### 2. Source Code Repository with Technical Documentation

Includes README, setup instructions, and integration details.

**Locations:**

- [README.md](../README.md) — Project overview, quick start, feature list
- [docs/setup-guide.md](setup-guide.md) — Complete setup instructions
- [docs/api-reference.md](api-reference.md) — Full API endpoint documentation

**Repository Structure:**

```
student-assistant-backend/
├── README.md                  # Project overview
├── docs/                      # All documentation
│   ├── architecture.md        # System architecture
│   ├── api-reference.md       # API endpoints
│   ├── setup-guide.md         # Installation guide
│   ├── requirements.md        # Project scope
│   ├── academic-integrity.md  # Guardrails documentation
│   ├── evaluation-plan.md     # Test cases
│   ├── artifacts.md           # This document
│   └── adrs/                  # Architecture decisions
├── src/app/                   # Application source code
├── examples/                  # Usage examples
└── notebooks/                 # Development notebooks
```

---

### 3. Examples of Generated Calendar Events & Study Sessions

Screenshots or exports showing tasks and study sessions created in Google Calendar.

**Evidence includes:**

- Study sessions auto-generated from course workload analysis
- Assignment reminders with 24-hour and 1-hour notifications
- Multi-day study plans distributed across the week
- Timezone-aware scheduling based on user's Google Calendar settings

**Location:** Screenshots collected during testing, available in project demonstration.

---

### 4. Examples of Generated Study Notes & Summaries

Sample notes stored in Notion demonstrating learning support features.

**Evidence includes:**

- Structured study notes with headings, bullet points, and key concepts
- Assignment tracker pages with due dates and status columns
- Study plan pages with prioritized topics and time blocks
- Course syllabus summaries with organized content

**Location:** Notion workspace exports collected during testing, available in project demonstration.

---

### 5. Demo Video or Screenshots of the System in Use

Visual evidence of the assistant's end-to-end functionality.

**Demo covers:**

- User registration and login flow
- Connecting Canvas, Google Calendar, and Notion integrations
- Chat interaction with streaming responses
- Course information queries
- Study session scheduling
- Note creation in Notion
- Academic integrity guardrail activation
- User settings and account management

**Location:** Video recording and screenshots in [evidence/](evidence/) folder.

---

### 6. React Frontend Application

A modern single-page application providing the user interface for Loop.

**Tech Stack:** React 19, TypeScript, Vite, Tailwind CSS v4, Radix UI, Zustand, TanStack Query

**Features:**

- Real-time AI chat interface with Markdown rendering and code syntax highlighting
- Integration settings dashboard for Canvas, Google Calendar, and Notion
- User profile management and security settings
- Protected routing with authentication guards
- Responsive, accessible design built with Radix UI primitives
- Optimistic UI updates and data caching via TanStack Query

**Repository:** [student-assistant-frontend](https://github.com/jorgechvz/student-assistant-frontend)  
**Deployment:** Netlify (frontend) / Render (backend)

---

## Artifact Checklist

| #   | Artifact                      | Type    | Status                    |
| --- | ----------------------------- | ------- | ------------------------- |
| 1   | Requirements & Scope          | Process | ✅ Complete — [requirements.md](requirements.md) |
| 2   | Architecture & Diagrams       | Process | ✅ Complete — [architecture.md](architecture.md) |
| 3   | Academic Integrity Guidelines | Process | ✅ Complete — [academic-integrity.md](academic-integrity.md) |
| 4   | Evaluation Plan & Test Cases  | Process | ✅ Complete — [evaluation-plan.md](evaluation-plan.md) |
| 5   | Architecture Decision Records | Process | ✅ Complete — [adrs/](adrs/README.md) |
| 6   | Working Prototype             | Final   | ✅ Complete — Live on Netlify + Render |
| 7   | Source Code + Documentation   | Final   | ✅ Complete — [Backend repo](../README.md) + [Frontend repo](https://github.com/jorgechvz/student-assistant-frontend) |
| 8   | Calendar Event Examples       | Final   | ✅ Screenshots — [evidence/google-calendar/](evidence/google-calendar/) |
| 9   | Study Note Examples           | Final   | ✅ Screenshots — [evidence/notion/](evidence/notion/) |
| 10  | Demo Video / Screenshots      | Final   | ✅ Screenshots — [evidence/](evidence/) + Demo Video |
