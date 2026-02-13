# ADR-003: MongoDB with Beanie ODM

## Status

Accepted

## Context

The application needs to persist:
- User accounts and credentials.
- OAuth tokens for three integrations (Canvas, Google, Notion).
- Chat sessions and message history.

The data is document-oriented: each user has independent token documents, chat sessions contain ordered message lists, and token schemas vary per integration. We needed a database that:
- Handles flexible, schema-evolving documents.
- Supports async operations for a FastAPI application.
- Provides good developer experience with Python type hints.

## Decision

We chose **MongoDB** as the database with **Motor** (async driver) and **Beanie** (ODM).

- **MongoDB** naturally fits the document-oriented data model — each integration token is a self-contained document linked by `user_id`.
- **Motor** provides native async/await support compatible with FastAPI's async request handling.
- **Beanie** provides Pydantic-based document models with automatic validation, indexing, and CRUD operations.

Six document collections:
- `users` — User accounts
- `canvas_tokens` — Canvas LMS API tokens
- `google_tokens` — Google OAuth tokens
- `notion_tokens` — Notion OAuth tokens
- `chat_sessions` — Conversation sessions
- `messages` — Individual chat messages

## Consequences

### Positive
- Beanie models inherit from Pydantic's `BaseModel`, providing automatic validation and JSON serialization — no separate schema layer needed.
- Async operations throughout (Motor) prevent blocking the event loop during DB calls.
- Schema flexibility allows integration tokens to have different fields without migration complexity.
- Indexes on `user_id` and `email` ensure fast lookups.
- Beanie's `Document` class provides built-in CRUD methods (`insert`, `save`, `delete`, `find`).

### Negative
- No relational integrity enforcement — `user_id` references between collections are application-managed.
- Account deletion requires manually cascading deletes across all related collections.
- MongoDB Atlas is required for production (local MongoDB for development).
- Beanie's `_to_entity` pattern adds some boilerplate to repository implementations.
