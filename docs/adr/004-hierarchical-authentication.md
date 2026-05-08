# ADR-004: Hierarchical Authentication (OIDC → API Key → Open)

**Status:** Accepted  
**Date:** 2025-02-05  
**Deciders:** Vectaris core team

---

## Context

The observability API must be securable for production while remaining frictionless
for local development and CI. A single hard-coded auth strategy would force all
environments into the most restrictive mode.

Requirements:
- Production: Bearer token from an enterprise identity provider (Azure Entra ID, Okta,
  Auth0)
- CI / integration tests: simple static API key without an IdP
- Local dev / demos: no auth overhead

## Decision

Implement a **hierarchical auth middleware** in `app/auth.py` + `app/oidc.py`:

1. **OIDC** — if `OIDC_ISSUER` env var is set, validate `Authorization: Bearer <JWT>`
   against the issuer's JWKS endpoint using `PyJWKClient`. Extracts `sub` + `tenant_id`
   claims for rate limiting.
2. **API Key** — if `API_KEY` env var is set (and OIDC is not), validate
   `X-API-Key: <key>` header with `secrets.compare_digest` (constant-time comparison).
3. **Open** — if neither env var is set, all requests pass through (development only).
   A warning is logged at startup.

The active mode is logged at application startup so operators know which path is in use.

## Consequences

**Positive:**
- Single middleware handles all auth modes; no code changes when promoting from dev
  to production.
- OIDC + JWKS supports key rotation without redeployment.
- `secrets.compare_digest` prevents timing-attack enumeration of API keys.
- Per-tenant `tenant_id` from JWT claims flows into rate limiting and quota
  enforcement.

**Negative / trade-offs:**
- Open mode is a footgun if accidentally deployed to production. Mitigated by
  the startup warning and by ensuring `API_KEY` or `OIDC_ISSUER` is always set
  in Helm/Bicep deployment templates.
- OIDC JWKS fetch adds ~50 ms to the first request after startup. Subsequent
  requests use the cached signing keys.

## Security Notes

- Never set `API_KEY` to a predictable value like `"secret"`.
- In Kubernetes, store `API_KEY` or `OIDC_ISSUER` in a Kubernetes `Secret`
  (see `deploy/helm/vectaris/templates/secret.yaml`).
- Rotate API keys by updating the secret and performing a rolling restart.
