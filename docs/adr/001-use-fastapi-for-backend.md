# ADR-001: Use FastAPI for the Observability Backend

**Status:** Accepted  
**Date:** 2025-01-15  
**Deciders:** Vectaris core team

---

## Context

We needed a Python web framework to serve the observability API. The primary
requirements were:

- Async-first to handle many concurrent SSE streams and outbound HTTP calls
  (Prometheus, Azure Cost Management, OpenAI billing)
- Automatic OpenAPI/Swagger documentation from type annotations
- First-class Pydantic v2 integration for request/response validation
- Good ecosystem for OpenTelemetry instrumentation
- Low boilerplate for CRUD endpoints and middleware

Candidates evaluated: **FastAPI**, Django REST Framework, Flask, Starlette (bare).

## Decision

Use **FastAPI** backed by **Uvicorn/Hypercorn** ASGI server.

## Consequences

**Positive:**
- `async`/`await` throughout allows hundreds of concurrent SSE clients without
  thread-pool overhead.
- Pydantic v2 models serve as both the schema validation layer and the response
  serialization layer — a single source of truth.
- Auto-generated `/docs` (Swagger UI) and `/redoc` without extra configuration.
- `opentelemetry-instrumentation-fastapi` provides zero-config request tracing.
- Middleware (CORS, auth, request context) is straightforward with `BaseHTTPMiddleware`.

**Negative / trade-offs:**
- FastAPI has less "batteries-included" than Django (no ORM, no admin panel).
  Acceptable because we deliberately keep the backend stateless and delegate
  storage to Prometheus / external cost APIs.
- Slightly more boilerplate for dependency injection compared to Flask extensions.
- Hot-reload in production requires careful Uvicorn configuration.

## Alternatives Considered

| Framework | Rejected because |
|-----------|-----------------|
| Django REST Framework | Heavier sync-first model; ORM and admin overhead not needed |
| Flask | No native async; `flask-restx` adds complexity |
| Starlette (bare) | FastAPI is Starlette + Pydantic — no reason to forgo the DX |
