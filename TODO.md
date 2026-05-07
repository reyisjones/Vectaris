# TODO — Prioritized Backlog

Legend: **P0** = blocks production · **P1** = next sprint · **P2** = nice-to-have
Items marked `[x]` were completed in the most recent iteration; `[ ]` items are pending.

## Backend

- [x] **P0** Replace stub `metrics_service`, `cost_service`, `agent_service` with real data sources (Azure Monitor / PromQL / cost APIs) — _Prometheus adapter (PromQL) + OpenAI billing adapter shipped; stub fallback when unconfigured; `data_source` field in all responses_
- [x] **P0** Persist agent registry (Postgres / Cosmos DB) and add `POST /agents` for registration — _in-memory dict registry with `POST /agents`, `DELETE /agents/{id}`, `PATCH /agents/{id}/heartbeat`_
- [x] **P0** Add API authentication (API key middleware via `X-API-Key`, opt-in through `API_KEY` env var) — _shipped in `app/auth.py`_
- [x] **P0** Replace static API key with OIDC / Azure Managed Identity — _`app/oidc.py` with PyJWKClient; OIDC > API key > open mode selection; supports Azure Entra ID, Okta, Auth0_
- [x] **P1** Configurable alert rules via YAML or `/alerts` admin endpoint — _`deploy/alert_rules.yaml` seed file + `GET/PUT/DELETE /api/v1/alerts/rules/{id}` CRUD API_
- [x] **P1** Background scheduler (APScheduler) for periodic alert evaluation + webhook delivery — _`app/scheduler.py` with HMAC-SHA256 webhook signing_
- [x] **P1** `/api/v1/llm/chat` proxy with token + latency capture for any OpenAI-compatible runtime — _`POST /api/v1/llm/chat` with OTel context propagation_
- [x] **P1** Cost-source adapters: Azure Cost Management, AWS CUR, OpenAI billing — _Azure CM OAuth2 + AWS SigV4 adapters (pure httpx, no boto3)_
- [x] **P2** Rate limiting (slowapi) + per-tenant quotas — _slowapi with Redis/memory storage; 1000/min global, 100/min per user, 20/min for LLM proxy; monthly tenant quotas with GET /api/v1/llm/quota endpoint_
- [ ] **P2** GraphQL gateway alongside REST
- [ ] **P2** SSE / WebSocket stream for live metrics push (replace polling)

## Frontend

- [x] **P0** Replace inline-style remnants in chart tooltips with theme variables — _shipped in `components/chartTheme.ts`_
- [x] **P0** Add error boundaries around route outlet — _shipped in `components/ErrorBoundary.tsx`_
- [x] **P1** Time-range selector on Dashboard (1h / 24h / 7d / 30d) — _`components/TimeRangeSelector.tsx` on Dashboard and Costs pages_
- [x] **P1** Per-model drill-down page (latency history, error timeline) — _`pages/ModelPage.tsx` at `/models/:modelName`_
- [x] **P1** Cost forecast tuning (horizon picker, scenarios) — _7/30/60/90 day horizon picker on Costs page_
- [x] **P1** Toast notifications for new critical alerts — _`components/ToastContainer.tsx` + `ToastContext.tsx` polling alerts every 15s_
- [x] **P1** Surface API key field in a settings page (read from `localStorage`, sent as `X-API-Key`) — _`pages/SettingsPage.tsx` with show/hide/save/clear_
- [x] **P2** Light theme + system preference detection — _`components/ThemeContext.tsx` + `ThemeToggle.tsx` with light/dark/system modes; CSS variables for both themes_
- [x] **P2** PWA manifest + offline cached last-known-good telemetry — _`manifest.json` + service worker with cache-first static assets and network-first API with offline fallback_
- [ ] **P2** Vitest coverage for components (snapshot + interaction)

## Telemetry & Ops

- [x] **P0** Wire OTel context into `httpx` client used by `llm_runtime_service` — _`propagate.inject` injects trace context into request headers; also fixed malformed function body in `llm_runtime_service.py`_
- [x] **P0** Add Grafana dashboard JSON in `deploy/grafana/` — _`vectaris-dashboard.json` with 5 stat KPI panels, LLM latency p50/p95/p99, agent health table, cost tracking, API rate/latency; provisioning YAML included_
- [x] **P1** Prometheus ServiceMonitor CRD in `deploy/kubernetes/` — _`servicemonitor.yaml` targeting backend `/metrics` endpoint_
- [x] **P1** Frontend Web Vitals → OTel Browser SDK → backend ingest — _`src/telemetry.ts` with OTel WebTracerProvider + web-vitals (LCP/CLS/INP/FID/FCP/TTFB)_
- [ ] **P2** Distributed tracing demo with OpenAI mock + Ollama

## Infra & CI

- [x] **P0** Generate and commit `frontend/package-lock.json` so CI can use `npm ci` — _committed_
- [x] **P0** Add `pip-audit` and `npm audit --audit-level=high` to CI — _shipped in `.github/workflows/ci.yml`_
- [x] **P0** Promote frontend lint from `|| true` to a hard CI failure — _shipped_
- [x] **P1** Add Dependabot config for pip + npm + actions — _`.github/dependabot.yml` with weekly schedule_
- [x] **P1** Add Bicep templates under `deploy/azure/` — _`main.bicep` (sub-scope) + `app.bicep` (ACR, Key Vault, Log Analytics, Container Apps)_
- [x] **P1** Frontend `Deployment + Service + Ingress` manifests — _`deploy/kubernetes/frontend.yaml` with ConfigMap, Service, and Ingress (nginx)_
- [x] **P2** Helm chart packaging — _`deploy/helm/vectaris/` with Chart.yaml, values.yaml, and complete template set (deployment, service, ingress, HPA, ServiceMonitor)_
- [x] **P2** Pre-commit hooks (ruff, prettier, mypy) — _`.pre-commit-config.yaml` with ruff, mypy, prettier, markdownlint; `backend/pyproject.toml` with tool configs; `scripts/setup-hooks.sh`_

## Documentation

- [x] **P1** `CONTRIBUTING.md` with branch / PR conventions — _shipped_
- [x] **P1** `SECURITY.md` with disclosure process — _shipped_
- [ ] **P2** ADR (Architecture Decision Records) folder
- [ ] **P2** Tutorial: instrumenting a custom AI agent for Vectaris
