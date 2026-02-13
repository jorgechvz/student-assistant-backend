# ADR-010: Prompt-Level Academic Integrity Guardrails

## Status

Accepted

## Context

The assistant has access to powerful tools (Canvas course data, Google Calendar, Notion) and a capable language model. Without guardrails, students could potentially:
- Ask the assistant to solve homework problems.
- Request essay writing or code generation for assignments.
- Use the assistant to find quiz/exam answers.

Academic integrity is a **non-negotiable requirement** for an educational tool. We needed a mechanism that:
- Prevents the assistant from completing academic work.
- Is consistent across all interactions.
- Cannot be bypassed through prompt injection or clever phrasing.
- Still allows the assistant to be helpful for learning.

## Decision

We implemented **prompt-level guardrails** as the primary defense mechanism:

1. **Guardrails are loaded first** in the system prompt, before any tool instructions. This establishes ethical boundaries as the highest-priority directive.

2. **Five non-negotiable principles** are defined:
   - NEVER solve homework/quizzes/exams.
   - NEVER write essays or complete assignments.
   - NEVER provide direct answers to assessments.
   - ALWAYS suggest strategies and resources.
   - ALWAYS empower independent learning.

3. **Redirection scripts** are embedded for common misuse patterns (homework requests, essay writing, exam answers). These follow an Acknowledge → Redirect → Offer Alternatives pattern.

4. **Validation** through 15 predefined misuse test scenarios that are periodically tested against the system.

The approach is prompt-based (not code-based filtering) because:
- The model needs to understand *why* certain requests are restricted to respond helpfully.
- Code-based keyword filtering would produce false positives ("help me with my homework" could mean "help me plan study time for homework").
- The redirection pattern requires contextual understanding that only the model can provide.

## Consequences

### Positive
- The model understands the intent behind restrictions, allowing nuanced responses.
- Redirection to tool-based alternatives keeps the interaction productive.
- The three-step pattern (Acknowledge → Redirect → Offer) is non-judgmental and student-friendly.
- Guardrails are in template files, making them easy to review and update.
- The model can distinguish between "solve this for me" and "help me understand this."

### Negative
- Prompt-based guardrails are not 100% guaranteed — sophisticated prompt injection could potentially bypass them.
- No server-side output validation to catch guardrail failures after generation.
- Effectiveness depends on the underlying model's instruction-following capability.
- Guardrails consume tokens in the system prompt, reducing available context for conversation.

### Future Improvements
- Add output validation layer to scan responses for potential violations.
- Implement Azure OpenAI content filters as a secondary safety net.
- Log and review flagged interactions for continuous guardrail refinement.
