# ADR-005: Server-Sent Events for Chat Streaming

## Status

Accepted

## Context

The AI assistant generates responses that can take several seconds to complete (especially when tool calls are involved). Without streaming, users would see a loading spinner for the entire duration, resulting in a poor user experience.

We needed a mechanism to deliver response tokens to the frontend as they are generated. Options considered:

1. **WebSockets** — Full-duplex, but adds complexity (connection management, reconnection logic).
2. **Server-Sent Events (SSE)** — Unidirectional server-to-client streaming over HTTP.
3. **Long polling** — Simple but inefficient.
4. **HTTP/2 Server Push** — Limited browser support for this use case.

## Decision

We chose **Server-Sent Events (SSE)** for streaming chat responses.

The implementation uses FastAPI's `StreamingResponse` with `text/event-stream` content type:

1. Frontend sends a `POST /chat/stream` request with the user's message.
2. Backend creates an `asyncio.Queue` as a bridge between the LangChain agent and the SSE generator.
3. LangChain's `astream_events` pushes tokens to the queue as a callback.
4. The SSE generator reads from the queue and yields `data: {...}\n\n` lines.

Three event types are sent:
- `{"type": "session", "session_id": "..."}` — First event, provides the session ID.
- `{"type": "token", "content": "..."}` — Each generated token.
- `{"type": "done"}` — Signals completion.

## Consequences

### Positive
- Users see the response being typed in real-time, dramatically improving perceived responsiveness.
- SSE is built on standard HTTP — works through proxies, load balancers, and CDNs without special configuration.
- Simpler than WebSockets: no connection upgrade, no heartbeat management.
- LangChain's `astream_events` natively supports async iteration, mapping cleanly to SSE.
- Frontend implementation is straightforward with the `EventSource` API or `fetch` with readable streams.

### Negative
- Unidirectional: the user cannot send messages while a response is streaming (acceptable for chat UX).
- SSE connections count against browser connection limits per domain (6 in HTTP/1.1).
- Error handling during streaming requires the frontend to detect broken connections and retry.
- The `asyncio.Queue` bridge adds complexity to the streaming endpoint.
