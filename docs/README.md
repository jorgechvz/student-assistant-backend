# Documentation Index

Welcome to the **Loop — Student Learning Assistant** documentation. This directory contains all technical and project documentation for the backend system.

---

## Project Deliverables

| Document                                | Description                                                    |
| --------------------------------------- | -------------------------------------------------------------- |
| [Requirements & Scope](requirements.md) | Project goals, assumptions, constraints, measurable objectives |
| [Project Artifacts](artifacts.md)       | Complete catalog of process and final deliverables             |
| [Evidence Screenshots](evidence/)       | Organized screenshots by feature area                          |

## Technical Documentation

| Document                          | Description                                                     |
| --------------------------------- | --------------------------------------------------------------- |
| [Architecture](architecture.md)   | System architecture, component diagrams, data flows, tech stack |
| [API Reference](api-reference.md) | Complete endpoint documentation with request/response examples  |
| [Setup Guide](setup-guide.md)     | Installation, configuration, and deployment instructions        |

## Safety & Quality

| Document                                    | Description                                            |
| ------------------------------------------- | ------------------------------------------------------ |
| [Academic Integrity](academic-integrity.md) | Guardrails, restricted behaviors, misuse prevention    |
| [Evaluation Plan](evaluation-plan.md)       | Test case definitions, benchmarks, scoring methodology |
| [Evaluation Results](evaluation-results.md) | Executed test results with evidence and scores         |

## Architecture Decisions

| ADR                                                  | Title                                                   |
| ---------------------------------------------------- | ------------------------------------------------------- |
| [ADR-001](adrs/001-layered-architecture.md)          | Layered Architecture with Clean Architecture Principles |
| [ADR-002](adrs/002-azure-openai-langchain.md)        | Azure OpenAI with LangChain Agent Framework             |
| [ADR-003](adrs/003-mongodb-beanie.md)                | MongoDB with Beanie ODM                                 |
| [ADR-004](adrs/004-jwt-httponly-cookies.md)          | JWT Authentication with HttpOnly Cookies                |
| [ADR-005](adrs/005-sse-streaming.md)                 | Server-Sent Events for Chat Streaming                   |
| [ADR-006](adrs/006-template-based-prompts.md)        | Template-Based Prompt Management                        |
| [ADR-007](adrs/007-tool-based-integrations.md)       | LangChain Tool-Based Integration Pattern                |
| [ADR-008](adrs/008-dynamic-tool-resolution.md)       | Dynamic Tool Resolution Per User                        |
| [ADR-009](adrs/009-canvas-personal-tokens.md)        | Canvas LMS Personal Access Tokens vs OAuth              |
| [ADR-010](adrs/010-academic-integrity-guardrails.md) | Prompt-Level Academic Integrity Guardrails              |

---

## How to Use This Documentation

- **New to the project?** Start with the [Requirements](requirements.md) and [Architecture](architecture.md).
- **Setting up locally?** Follow the [Setup Guide](setup-guide.md).
- **Building a frontend?** Reference the [API Reference](api-reference.md).
- **Reviewing the project?** Check [Evaluation Results](evaluation-results.md) and [Artifacts](artifacts.md).
- **Understanding a design decision?** Browse the [ADRs](adrs/README.md).
