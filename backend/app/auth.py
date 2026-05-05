"""Authentication middleware supporting both static API key and OIDC JWT modes.

Auth mode selection (evaluated in order):
1. **OIDC mode** — ``OIDC_ISSUER`` is non-empty.  Requests must supply an
   ``Authorization: Bearer <JWT>`` header.  The token is validated against the
   issuer's JWKS endpoint (auto-discovered via ``.well-known/openid-configuration``
   unless ``OIDC_JWKS_URI`` is set explicitly).  Works with Azure Entra ID,
   Okta, Auth0, Keycloak, and any other OIDC-compliant provider.

2. **API key mode** — ``API_KEY`` is non-empty (and ``OIDC_ISSUER`` is empty).
   Requests must supply ``X-API-Key: <key>`` (header name configurable via
   ``API_KEY_HEADER``).  Kept for local / on-prem deployments.

3. **Open mode** — neither is set.  All requests pass (development default).

Public paths (``/health``, ``/ready``, ``/metrics``, OpenAPI docs) are always
exempt from authentication.
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
    return path.startswith("/docs/") or path.startswith("/redoc/")


def _unauthorized(reason: str, path: str) -> JSONResponse:
    _log.warning("auth.rejected", path=path, reason=reason)
    return JSONResponse(
        status_code=401,
        content={"detail": "Unauthorized"},
        headers={"WWW-Authenticate": "Bearer"},
    )


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Unified authentication middleware (API key and/or OIDC Bearer JWT)."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if request.method == "OPTIONS" or _is_public(request.url.path):
            return await call_next(request)

        # --- OIDC JWT mode ---
        if settings.oidc_issuer:
            return await self._check_oidc(request, call_next)

        # --- Static API key mode ---
        if settings.api_key:
            return await self._check_api_key(request, call_next)

        # --- Open / dev mode ---
        return await call_next(request)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _check_oidc(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        from jwt import InvalidTokenError

        from app.oidc import validate_bearer_token

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return _unauthorized("missing_bearer_token", request.url.path)

        token = auth_header[len("Bearer "):]
        try:
            claims = validate_bearer_token(token)
        except InvalidTokenError as exc:
            _log.warning(
                "auth.oidc_rejected",
                path=request.url.path,
                error=str(exc),
            )
            return _unauthorized("invalid_token", request.url.path)

        # Attach verified claims to request state for downstream handlers.
        request.state.auth_claims = claims
        return await call_next(request)

    async def _check_api_key(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        provided = request.headers.get(settings.api_key_header)
        if provided != settings.api_key:
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
