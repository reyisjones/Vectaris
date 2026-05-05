# TODO — Prioritized Backlog

Legend: **P0** = blocks production · **P1** = next sprint · **P2** = nice-to-have
Items marked `[x]` were completed in the most recent iteration; `[ ]` items are pending.

## Backend

- [ ] **P0** Replace stub `metrics_service`, `cost_service`, `agent_service` with real data sources (Azure Monitor / PromQL / cost APIs)
- [ ] **P0** Persist agent registry (Postgres / Cosmos DB) and add `POST /agents` for registration
- [x] **P0** Add API authentication (API key middleware via `X-API-Key`, opt-in through `API_KEY` env var) — _shipped in `app/auth.py`_
- [ ] **P0** Replace static API key with OIDC / Azure Managed Identity
- [ ] **P1** Configurable alert rules via YAML or `/alerts` admin endpoint
- [ ] **P1** Background scheduler (APScheduler) for periodic alert evaluation + webhook delivery
- [ ] **P1** `/api/v1/llm/chat` proxy with token + latency capture for any OpenAI-compatible runtime
- [ ] **P1** Cost-source adapters: Azure Cost Management, AWS CUR, OpenAI billing
- [ ] **P2** Rate limiting (slowapi) + per-tenant quotas
- [ ] **P2** GraphQL gateway alongside REST
- [ ] **P2** SSE / WebSocket stream for live metrics push (replace polling)

## Frontend

- [x] **P0** Replace inline-style remnants in chart tooltips with theme variables — _shipped in `components/chartTheme.ts`_
- [x] **P0** Add error boundaries around route outlet — _shipped in `components/ErrorBoundary.tsx`_
- [ ] **P1** Time-range selector on Dashboard (1h / 24h / 7d / 30d)
- [ ] **P1** Per-model drill-down page (latency history, error timeline)
- [ ] **P1** Cost forecast tuning (horizon picker, scenarios)
- [ ] **P1** Toast notifications for new critical alerts
- [ ] **P1** Surface API key field in a settings page (read from `localStorage`, sent as `X-API-Key`)
- [ ] **P2** Light theme + system preference detection
- [ ] **P2** PWA manifest + offline cached last-known-good telemetry
- [ ] **P2** Vitest coverage for components (snapshot + interaction)

## Telemetry & Ops

- [ ] **P0** Wire OTel context into `httpx` client used by `llm_runtime_service`
- [ ] **P0** Add Grafana dashboard JSON in `deploy/grafana/`
- [ ] **P1** Prometheus ServiceMonitor CRD in `deploy/kubernetes/`
- [ ] **P1** Frontend Web Vitals → OTel Browser SDK → backend ingest
- [ ] **P2** Distributed tracing demo with OpenAI mock + Ollama

## Infra & CI

- [x] **P0** Generate and commit `frontend/package-lock.json` so CI can use `npm ci` — _committed_
- [x] **P0** Add `pip-audit` and `npm audit --audit-level=high` to CI — _shipped in `.github/workflows/ci.yml`_
- [x] **P0** Promote frontend lint from `|| true` to a hard CI failure — _shipped_
- [ ] **P1** Add Dependabot config for pip + npm + actions
- [ ] **P1** Add Bicep templates under `deploy/azure/`
- [ ] **P1** Frontend `Deployment + Service + Ingress` manifests
- [ ] **P2** Helm chart packaging
- [ ] **P2** Pre-commit hooks (ruff, prettier, mypy)

## Documentation

- [x] **P1** `CONTRIBUTING.md` with branch / PR conventions — _shipped_
- [x] **P1** `SECURITY.md` with disclosure process — _shipped_
- [ ] **P2** ADR (Architecture Decision Records) folder
- [ ] **P2** Tutorial: instrumenting a custom AI agent for Vectaris
