# TODO — Prioritized Backlog

Legend: **P0** = blocks production · **P1** = next sprint · **P2** = nice-to-have

## Backend

- [ ] **P0** Replace stub `metrics_service`, `cost_service`, `agent_service` with real data sources (Azure Monitor / PromQL / cost APIs)
- [ ] **P0** Persist agent registry (Postgres / Cosmos DB) and add `POST /agents` for registration
- [ ] **P0** Add API authentication (API key middleware → OIDC / Azure Managed Identity)
- [ ] **P1** Configurable alert rules via YAML or `/alerts` admin endpoint
- [ ] **P1** Background scheduler (APScheduler) for periodic alert evaluation + webhook delivery
- [ ] **P1** Add `/api/v1/llm/chat` proxy with token + latency capture for any OpenAI-compatible runtime
- [ ] **P1** Add cost-source adapters: Azure Cost Management, AWS CUR, OpenAI billing
- [ ] **P2** Rate limiting (slowapi) + per-tenant quotas
- [ ] **P2** GraphQL gateway alongside REST
- [ ] **P2** SSE / WebSocket stream for live metrics push (replace polling)

## Frontend

- [ ] **P0** Replace inline-style remnants in chart tooltips with theme variables
- [ ] **P0** Add error boundaries around route outlet
- [ ] **P1** Time-range selector on Dashboard (1h / 24h / 7d / 30d)
- [ ] **P1** Per-model drill-down page (latency history, error timeline)
- [ ] **P1** Cost forecast tuning (horizon picker, scenarios)
- [ ] **P1** Toast notifications for new critical alerts
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

- [ ] **P0** Generate and commit `frontend/package-lock.json` (so CI can use `npm ci`)
- [ ] **P0** Add `pip-audit` and `npm audit --audit-level=high` to CI
- [ ] **P1** Add Dependabot config for pip + npm + actions
- [ ] **P1** Add Bicep templates under `deploy/azure/`
- [ ] **P1** Frontend `Deployment + Service + Ingress` manifests
- [ ] **P2** Helm chart packaging
- [ ] **P2** Pre-commit hooks (ruff, prettier, mypy)

## Documentation

- [ ] **P1** `CONTRIBUTING.md` with branch/PR conventions
- [ ] **P1** `SECURITY.md` with disclosure process
- [ ] **P2** ADR (Architecture Decision Records) folder
- [ ] **P2** Tutorial: instrumenting a custom AI agent for Vectaris
