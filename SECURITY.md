# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| `main`  | ✅ |
| Previous tagged releases | Best-effort |

## Reporting a Vulnerability

If you believe you've found a security vulnerability in Vectaris, please
**do not open a public GitHub issue**. Instead, send a detailed report to:

**security@vectaris.dev** (or open a private GitHub Security Advisory)

Include:

- A description of the issue and the impact
- Reproduction steps or a proof-of-concept
- The affected commit or release
- Your name and contact info (for credit, optional)

You should receive an acknowledgement within **3 business days** and a
status update within **7 business days**.

## Disclosure Process

1. We confirm the vulnerability and determine its scope.
2. We prepare a fix on a private branch.
3. We coordinate a disclosure date with you.
4. We release the patch and publish a security advisory crediting the reporter.

## Security Hardening Already in Place

- API key authentication middleware (opt-in via `API_KEY` env var)
- CORS allow-list (no wildcards in production)
- Pydantic v2 strict input validation
- Structured logging with no PII or secrets
- Non-root container users with read-only filesystems
- Liveness / readiness probes with resource limits in Kubernetes
- Dependency audits in CI (`pip-audit`, `npm audit`)

## Scope

In scope:

- Backend HTTP API (`backend/app/**`)
- Frontend application (`frontend/src/**`)
- Docker images and Kubernetes manifests
- CI/CD configuration

Out of scope:

- Self-hosted deployments and their network configuration
- Third-party dependencies (please report upstream)
- Social engineering or physical security

Thank you for helping keep Vectaris and its users safe.
