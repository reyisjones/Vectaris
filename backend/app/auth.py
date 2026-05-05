"""Optional API key authentication middleware.

When `settings.api_key` is empty (default), the middleware is a no-op so the
service stays usable in development. When a key is configured, every request
to a protected path must carry the configured header (default: `X-API-Key`).

Public paths (health, readiness, Prometheus metrics, OpenAPI/Swagger) remain
unauthenticated.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.config import settings

_log = structlog.get_logger("auth")

PUBLIC_PATHS: frozenset[str] = frozenset(
    {
        "/health",
        "/ready",
        "/metrics",
        "/docs",
        "/redoc",
        "/openapi.json",
    }
)


def _is_public(path: str) -> bool:
    if path in PUBLIC_PATHS:
        return True
    # static assets served by FastAPI docs (e.g. /docs/oauth2-redirect)
    return path.startswith("/docs/") or path.startswith("/redoc/")


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Enforce a static API key on protected paths when one is configured."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        configured = settings.api_key
        if not configured:
            return await call_next(request)

        if request.method == "OPTIONS" or _is_public(request.url.path):
            return await call_next(request)

        provided = request.headers.get(settings.api_key_header)
        if provided != configured:
            _log.warning(
                "auth.rejected",
                path=request.url.path,
                reason="missing_or_invalid_api_key",
            )
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or missing API key"},
            )

        return await call_next(request)
