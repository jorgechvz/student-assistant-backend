# Architecture Decision Records

This directory contains the Architecture Decision Records (ADRs) for the Student Learning Assistant (Loop) project.

ADRs document the significant architectural decisions made during the development of this project, including their context, the decision itself, and the consequences.

## Index

| ADR | Title | Status |
|-----|-------|--------|
| [ADR-001](001-layered-architecture.md) | Layered Architecture with Clean Architecture Principles | Accepted |
| [ADR-002](002-azure-openai-langchain.md) | Azure OpenAI with LangChain Agent Framework | Accepted |
| [ADR-003](003-mongodb-beanie.md) | MongoDB with Beanie ODM | Accepted |
| [ADR-004](004-jwt-httponly-cookies.md) | JWT Authentication with HttpOnly Cookies | Accepted |
| [ADR-005](005-sse-streaming.md) | Server-Sent Events for Chat Streaming | Accepted |
| [ADR-006](006-template-based-prompts.md) | Template-Based Prompt Management | Accepted |
| [ADR-007](007-tool-based-integrations.md) | LangChain Tool-Based Integration Pattern | Accepted |
| [ADR-008](008-dynamic-tool-resolution.md) | Dynamic Tool Resolution Per User | Accepted |
| [ADR-009](009-canvas-personal-tokens.md) | Canvas LMS Personal Access Tokens vs OAuth | Accepted |
| [ADR-010](010-academic-integrity-guardrails.md) | Prompt-Level Academic Integrity Guardrails | Accepted |

## ADR Template

```markdown
# ADR-NNN: Title

## Status
Accepted | Deprecated | Superseded by ADR-NNN

## Context
What is the issue that we're seeing that motivates this decision?

## Decision
What is the change that we're proposing and/or doing?

## Consequences
What becomes easier or more difficult because of this change?
```
