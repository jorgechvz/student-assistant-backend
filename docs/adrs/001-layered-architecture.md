# ADR-001: Layered Architecture with Clean Architecture Principles

## Status

Accepted

## Context

The Student Learning Assistant integrates multiple external services (Canvas LMS, Google Calendar, Notion, Azure OpenAI), manages user authentication, and orchestrates an AI agent. Without clear architectural boundaries, the codebase would become tightly coupled, making it difficult to test individual components, swap implementations, or onboard new contributors.

We needed an architecture that:
- Separates business logic from infrastructure concerns.
- Allows external service implementations to be replaced without affecting core logic.
- Provides clear dependency direction.
- Supports the complexity of an AI agent with multiple tool integrations.

## Decision

We adopted a **layered architecture** inspired by Clean Architecture and Hexagonal Architecture (Ports and Adapters):

```
API Layer → Application Layer → Domain Layer ← Infrastructure Layer
```

- **API Layer** (`api/`): FastAPI routes, dependencies, request/response schemas. Handles HTTP concerns exclusively.
- **Application Layer** (`application/`): Services and use cases containing business logic orchestration.
- **Domain Layer** (`domain/`): Core models, repository interfaces (ports), and tool definitions. Has zero dependencies on outer layers.
- **Infrastructure Layer** (`infrastructure/`): Concrete implementations of ports — database repos, API adapters, security utilities.

Repository interfaces are defined in the domain layer and implemented in infrastructure, following the Dependency Inversion Principle.

## Consequences

### Positive
- External services (MongoDB, Azure OpenAI, Canvas API) can be swapped by implementing new adapters without modifying business logic.
- Business logic in services is testable in isolation using mock implementations of ports.
- Clear separation of concerns makes the codebase navigable.
- New integrations (e.g., adding Todoist or Slack) would only require a new adapter and tool definition.

### Negative
- Additional boilerplate for interface definitions and adapter classes.
- Some indirection when tracing request flow through layers.
- The use-case layer is thin (mostly pass-through) for simpler operations, adding minimal value in those cases.
