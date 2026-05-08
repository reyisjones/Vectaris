# ADR-005: Use Server-Sent Events Instead of WebSockets for Live Metrics

**Status:** Accepted  
**Date:** 2025-04-10  
**Deciders:** Vectaris core team

---

## Context

The dashboard needs to display metrics that update in near-real time (every 5 seconds)
without the user manually refreshing. Two primary push mechanisms were considered:
**Server-Sent Events (SSE)** and **WebSockets**.

## Decision

Use **Server-Sent Events** via `GET /api/v1/metrics/stream` (FastAPI `StreamingResponse`
with `media_type="text/event-stream"`) and the browser-native `EventSource` API.

## Rationale

| Factor | SSE | WebSocket |
|--------|-----|-----------|
| Direction | Server → client (unidirectional) | Bidirectional |
| Browser support | All modern browsers; native `EventSource` | All modern browsers |
| HTTP/2 multiplexing | Yes — many streams over one TCP connection | No — separate upgrade |
| Nginx/load-balancer support | Standard HTTP; no special config | Requires `Upgrade` header passthrough |
| Auto-reconnect | Built-in (`EventSource` retries automatically) | Manual reconnect logic |
| Implementation complexity | ~30 lines (server + client) | ~100 lines + ping/pong |
| Auth via headers | No (cookies or query param only) | Yes (headers on upgrade) |

Metrics streaming is **server → client only** — the client never needs to send data
on the same channel. SSE is the simpler, more robust choice for this use case.

The auth limitation (SSE doesn't support custom request headers after the initial
`EventSource` constructor) is acceptable because:
- In open/API-key mode the API key is passed as a query parameter or cookie.
- In OIDC mode the dashboard is deployed behind an ingress that validates the session
  cookie before the request reaches the backend.

## Consequences

**Positive:**
- `EventSource` handles reconnection automatically with exponential back-off.
- The `useMetricsStream` hook abstracts the connection behind a clean React API.
- No message framing or protocol negotiation overhead.
- Works through HTTP/2 load balancers without `Upgrade` support.
- `X-Accel-Buffering: no` header disables nginx response buffering so events
  are delivered immediately.

**Negative / trade-offs:**
- SSE is HTTP/1.1 limited to 6 concurrent connections per origin in some browsers
  (not a concern for an internal dashboard with a single `/stream` endpoint).
- If bidirectional communication is needed in the future (e.g., live config pushes
  from server + command execution from client), this ADR should be revisited in
  favor of WebSockets or a CRDT sync protocol.

## Alternatives Considered

| Option | Rejected because |
|--------|-----------------|
| Polling (React Query `refetchInterval`) | Higher server load; 30s latency floor |
| WebSockets | Bidirectional complexity not needed; harder to proxy |
| GraphQL Subscriptions | Heavy additional dependency (subscription transport) |
