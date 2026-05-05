"""OIDC JWT validation using PyJWT with JWKS auto-discovery and caching.

Supports any OIDC-compliant issuer (Azure Entra ID, Okta, Auth0, Keycloak, …).

Configuration
-------------
``OIDC_ISSUER``   — Required. e.g. ``https://login.microsoftonline.com/{tenant}/v2.0``
``OIDC_AUDIENCE`` — Required. The ``aud`` claim expected in the token.
``OIDC_JWKS_URI`` — Optional. Skip discovery; provide the JWKS endpoint directly.

Azure Managed Identity / Workload Identity
------------------------------------------
Tokens issued by Azure AD carry ``iss`` =
``https://login.microsoftonline.com/{tid}/v2.0`` and ``aud`` = the registered
app's client ID (or ``api://<app-id>``). Set those two values in config and
no further changes are needed — the public key is auto-discovered from the
standard ``.well-known/openid-configuration`` endpoint.
"""

from __future__ import annotations

import structlog
from jwt import InvalidTokenError, PyJWKClient, decode as jwt_decode

from app.config import settings

_log = structlog.get_logger("auth.oidc")

# PyJWKClient handles key caching internally.  A module-level singleton is
# used so the cache survives across requests (it refreshes automatically when
# a key is not found).
_jwks_client: PyJWKClient | None = None


def _get_jwks_client() -> PyJWKClient:
    """Return (creating if needed) the singleton JWKS client.

    The JWKS URI is either taken directly from ``settings.oidc_jwks_uri`` or
    constructed via the standard OIDC discovery endpoint.  Because discovery
    is a synchronous network call we perform it lazily on first use; subsequent
    calls are free since ``_jwks_client`` is already populated.

    Note: PyJWKClient makes a blocking HTTP call during ``get_signing_key_from_jwt``.
    This is acceptable because it only happens on cache misses (typically once
    per key rotation, usually days apart).  For a high-throughput service, wrap
    this in a thread pool executor; for a dashboard API the current approach is
    sufficient.
    """
    global _jwks_client
    if _jwks_client is not None:
        return _jwks_client

    jwks_uri = settings.oidc_jwks_uri
    if not jwks_uri:
        # Auto-discover from the OIDC well-known configuration endpoint.
        import urllib.request

        import json as _json

        discovery_url = (
            settings.oidc_issuer.rstrip("/") + "/.well-known/openid-configuration"
        )
        _log.info("oidc.discovery", url=discovery_url)
        with urllib.request.urlopen(discovery_url, timeout=10) as resp:  # noqa: S310
            doc = _json.loads(resp.read())
        jwks_uri = doc["jwks_uri"]
        _log.info("oidc.jwks_uri_resolved", jwks_uri=jwks_uri)

    _jwks_client = PyJWKClient(jwks_uri, cache_jwk_set=True, lifespan=3600)
    return _jwks_client


def validate_bearer_token(token: str) -> dict:
    """Validate a raw JWT string and return the decoded claims.

    Raises ``jwt.InvalidTokenError`` (or a subclass) on any validation failure.
    Callers should map this to an HTTP 401 response.
    """
    client = _get_jwks_client()
    signing_key = client.get_signing_key_from_jwt(token)

    options = {"require": ["exp", "iss"]}
    # Audience validation is skipped when oidc_audience is not configured so
    # the service can be used without registering an explicit audience claim.
    if settings.oidc_audience:
        options["require"].append("aud")

    claims = jwt_decode(
        token,
        signing_key.key,
        algorithms=["RS256", "RS384", "RS512", "ES256", "ES384", "ES512"],
        audience=settings.oidc_audience or None,
        issuer=settings.oidc_issuer,
        options=options,
    )
    return claims


def reset_jwks_client() -> None:
    """Reset the cached JWKS client (useful in tests or after config changes)."""
    global _jwks_client
    _jwks_client = None
