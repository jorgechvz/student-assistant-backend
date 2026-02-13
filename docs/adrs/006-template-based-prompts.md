# ADR-006: Template-Based Prompt Management

## Status

Accepted

## Context

The AI assistant's behavior is defined by its system prompt, which includes:
- Identity and personality ("Loop").
- Academic integrity guardrails.
- Tool usage instructions.
- Dynamic integration-awareness (which services are connected).

Initially, the system prompt was a hardcoded multi-line string inside `agent_service.py`. This caused several problems:
- Changes to the prompt required modifying Python code.
- The prompt was ~100 lines long, making the service file hard to read.
- Different prompt components (guardrails, tool instructions, fallback) were mixed together.
- No separation of concerns between behavior rules and implementation.

## Decision

We adopted a **template-based prompt management** system:

- A `PromptBuilder` class loads prompt templates from `.txt` files in `prompts/templates/`.
- Three template files:
  - `guardrails.txt` — Identity, personality, and academic integrity rules.
  - `student_assistant_system.txt` — Tool usage instructions (when integrations are connected).
  - `no_integrations_system.txt` — Fallback instructions (when no integrations are connected).
- `AgentService._get_default_system_prompt()` composes the final prompt by:
  1. Loading guardrails (always included first).
  2. Loading tool instructions (based on whether integrations exist).
  3. Dynamically detecting missing integrations by inspecting tool names.
  4. Appending per-integration connection suggestions for missing services.

Template loading uses `@lru_cache` for performance.

## Consequences

### Positive
- Prompts can be edited without touching Python code.
- Clear separation: guardrails (what NOT to do) vs. tool instructions (what TO do) vs. fallback (when nothing is connected).
- Dynamic composition means the system prompt adapts to each user's integration state.
- Templates are version-controlled alongside code.
- Easy to A/B test different prompt versions by swapping template files.

### Negative
- File I/O at startup (mitigated by `lru_cache`).
- Template variables (if needed) would require a templating engine or manual string formatting.
- The prompt composition logic in `_get_default_system_prompt()` is still code-based, mixing template loading with integration detection.
