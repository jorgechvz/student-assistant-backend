# ADR-002: Azure OpenAI with LangChain Agent Framework

## Status

Accepted

## Context

The assistant needs a large language model (LLM) capable of:
- Understanding natural language queries about courses, assignments, and schedules.
- Deciding which tools to invoke (Canvas, Google Calendar, Notion) based on user intent.
- Generating helpful, contextual responses.
- Streaming responses token-by-token for a responsive user experience.

We evaluated several options:
1. **Direct OpenAI API** — Simple but lacks agent orchestration for multi-tool scenarios.
2. **LangChain with OpenAI** — Provides agent framework with tool-calling support.
3. **Azure OpenAI with LangChain** — Enterprise-grade OpenAI with LangChain's orchestration.
4. **Custom agent loop** — Maximum control but significant development effort.

## Decision

We chose **Azure OpenAI** as the LLM provider with **LangChain** as the agent orchestration framework.

- **Azure OpenAI** provides enterprise SLA, data privacy compliance, and regional deployment (important for educational contexts).
- **LangChain's `create_react_agent`** handles the tool-calling loop: the model decides which tools to call, LangChain executes them, and feeds results back.
- Tools are defined using LangChain's `@tool` decorator with detailed docstrings that serve as the LLM's tool descriptions.
- The `AzureOpenAIAdapter` wraps LangChain's `AzureChatOpenAI` with retry logic (tenacity) for resilience.

## Consequences

### Positive
- Tool-calling is handled declaratively — adding a new tool only requires a `@tool` function.
- Azure OpenAI provides content filtering, responsible AI features, and data residency controls.
- LangChain handles the agent loop, reducing custom orchestration code.
- Streaming is natively supported via `astream_events`.
- Retry logic with exponential backoff handles transient API failures gracefully.

### Negative
- Dependency on LangChain's abstractions — breaking changes in LangChain require updates.
- Azure OpenAI pricing is token-based; costs scale with usage.
- LangChain's agent loop can be opaque when debugging unexpected tool-calling behavior.
- The adapter caches LLM instances keyed by parameters, which requires careful memory management.
