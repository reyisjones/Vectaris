# Architecture — Vectaris AI Platform Dashboard

## 1. System Overview

```
┌──────────────────────────────────────────────────────────────────────────┐
│                             User / Browser                               │
└─────────────────────────────────┬────────────────────────────────────────┘
                                  │ HTTPS
┌─────────────────────────────────▼────────────────────────────────────────┐
│                      React 18 SPA  (Vite + TypeScript)                   │
│                                                                          │
│  React Router v6   ─┬──  /             DashboardPage  (SSE live stream)  │
│                     ├──  /agents       AgentsPage                        │
│                     ├──  /models/:m    ModelPage  (drill-down)           │
│                     ├──  /costs        CostsPage  (+ forecast)           │
│                     ├──  /alerts       AlertsPage                        │
│                     ├──  /llm          LLMRuntimePage                    │
│                     └──  /settings     SettingsPage  (API key)           │
│                                                                          │
│  TanStack Query  →  services/api.ts (Axios + EventSource, typed)         │
│  useMetricsStream→  SSE /api/v1/metrics/stream  (auto-reconnect)         │
│  ThemeContext    →  light / dark / system preference + toggle            │
│  Recharts        →  LatencyChart, CostBreakdown                          │
│  OTel Browser    →  Web Vitals → backend OTLP ingest                     │
│  PWA             →  manifest + service worker (offline cache)            │
└─────────────────────────────────┬────────────────────────────────────────┘
                                  │ HTTP/JSON · SSE · GraphQL
┌─────────────────────────────────▼────────────────────────────────────────┐
│                FastAPI Backend  (Python 3.12, Pydantic v2)               │
│                                                                          │
│  Auth: OIDC (PyJWKClient) › API key (X-API-Key) › open                   │
│                                                                          │
│  Middleware stack                                                        │
│    ├─ RequestContextMiddleware  → request_id, structlog ctxvars,         │
│    │                              http_requests_total + duration hist    │
│    ├─ CORSMiddleware            → origin allowlist                       │
│    └─ slowapi rate limiter      → per-user + global limits               │
│                                                                          │
│  Routers (v1)                                                            │
│    /metrics/usage   /metrics/latency   /metrics/stream (SSE)            │
│    /agents          /agents/{id}/health                                  │
│    /costs           /costs/forecast                                      │
│    /alerts          /alerts/rules/{id}                                   │
│    /llm/runtime     /llm/chat          /llm/quota                        │
│    /health  /ready  /metrics  (Prometheus)                               │
│    /graphql  (Strawberry GraphQL + GraphiQL IDE)                         │
│                                                                          │
│  Service layer + APScheduler (alert eval + HMAC webhook fanout)          │
│    metrics_service · agent_service · cost_service · alert_service        │
│    llm_runtime_service · scheduler                                       │
│                                                                          │
│  Telemetry                                                               │
│    OTel TracerProvider + MeterProvider  → OTLP gRPC                      │
│    structlog → JSON stdout (trace_id correlated)                         │
│    prometheus_client  → /metrics                                         │
└─────────────┬────────────────────────────────────────┬───────────────────┘
              │                                        │
   ┌──────────▼─────────┐                  ┌───────────▼───────────┐
   │   OTLP Collector   │                  │  Ollama (optional)    │
   │ (Tempo/Jaeger/AzM) │                  │  /v1/chat  /api/tags  │
   └────────────────────┘                  └───────────────────────┘
```

## 2. Data Flow

```
AI workload  ─OTel SDK─►  OTLP collector  ─►  Azure Monitor / Tempo / Jaeger
                               │
                               ▼
                      Vectaris Backend  ──►  Prometheus scraper (/metrics)
                               │
                   ┌─────────┴─────────┐
             REST JSON API     SSE stream    GraphQL
                   │            │  (push)      │
                   ▼            ▼             ▼
              React SPA  ─►  TanStack Query + useMetricsStream hook
                               │
                               ▼
                             User UI
```

## 3. Request Lifecycle

1. Browser issues request — Axios attaches an optional `X-Request-ID`.
2. `RequestContextMiddleware` ensures an ID exists, binds `request_id` to structlog ctxvars.
3. Router validates with Pydantic → delegates to service layer → returns response model.
4. Counters/histograms updated with `(method, path, status)` labels.
5. Structured access log line is emitted (with `trace_id` when OTel is enabled).
6. Response carries `X-Request-ID` back for client-side correlation.

## 4. Component Architecture

### Frontend

| Layer | Files |
|-------|-------|
| Shell | `App.tsx`, `components/AppLayout.tsx`, `styles/global.css` |
| Context | `ThemeContext.tsx` (light/dark/system), `ToastContext.tsx` |
| Pages | `DashboardPage.tsx`, `AgentsPage.tsx`, `CostsPage.tsx`, `AlertsPage.tsx`, `LLMRuntimePage.tsx`, `ModelPage.tsx`, `SettingsPage.tsx` |
| Widgets | `MetricCard`, `LatencyChart`, `CostBreakdown`, `AgentHealthTable`, `AlertsList`, `LLMRuntimeCard`, `ThemeToggle`, `ToastContainer`, `TimeRangeSelector`, `StreamBadge` |
| Hooks | `useMetricsStream.ts` (SSE EventSource with auto-reconnect) |
| Data | `services/api.ts` (typed Axios + EventSource client + DTOs) |
| Telemetry | `telemetry.ts` (OTel WebTracerProvider + Web Vitals) |
| PWA | `public/manifest.json`, service worker (cache-first + offline fallback) |
| Tests | `src/test/` — 22 Vitest tests: MetricCard, AgentHealthTable, LatencyChart, useMetricsStream |

### Backend

| Module | Responsibility |
|--------|----------------|
| `app/main.py` | App factory, lifespan, exception handler, router mounting |
| `app/config.py` | pydantic-settings, env-driven |
| `app/auth.py` | API key middleware (`X-API-Key`) |
| `app/oidc.py` | OIDC/JWT validation via PyJWKClient (Azure AD, Okta, Auth0) |
| `app/scheduler.py` | APScheduler — periodic alert evaluation + HMAC-signed webhook fanout |
| `app/graphql_schema.py` | Strawberry GraphQL schema + resolvers |
| `app/logging_config.py` | structlog JSON pipeline + trace correlation |
| `app/middleware.py` | Request ID + Prometheus instrumentation + slowapi rate limiting |
| `app/routers/*` | Thin HTTP layer; no business logic |
| `app/services/*` | Pure-function business logic (metrics, agents, costs, alerts, LLM) |
| `app/models/*` | Pydantic schemas (request/response contracts) |
| `app/telemetry/setup.py` | OTel tracer + meter providers |

## 5. Deployment Topology

```
┌────────────────────────────────────────────────────────────────┐
│                        Azure Resource Group                    │
│                                                                │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐  │
│  │  Container   │    │  Container   │    │ Application      │  │
│  │  App (FE)    │───►│  App (BE)    │───►│ Insights / OTLP  │  │
│  │  nginx :80   │    │  uvicorn :8k │    │ ingestion        │  │
│  └──────────────┘    └──────┬───────┘    └──────────────────┘  │
│                             │                                  │
│                       ┌─────▼─────┐         ┌──────────────┐   │
│                       │ Key Vault │         │ ACR (images) │   │
│                       └───────────┘         └──────────────┘   │
└────────────────────────────────────────────────────────────────┘
```

Kubernetes (`deploy/kubernetes/backend.yaml`):

- non-root user, read-only root FS
- liveness `/health`, readiness `/ready`
- HPA: min 2 / max 10 / 70 % CPU
- Resources: 100 m / 256 Mi requests, 500 m / 512 Mi limits

## 6. Security

| Layer | Control |
|-------|---------|
| Transport | TLS 1.3 (terminated at ingress) |
| Auth | Hierarchical: OIDC (Azure Entra ID / Okta / Auth0) › API key (`X-API-Key`) › open |
| Rate limiting | slowapi: 1 000/min global, 100/min per user, 20/min LLM proxy |
| Tenant quotas | Monthly token cap per tenant, enforced by `GET /api/v1/llm/quota` |
| Secrets | Azure Key Vault — never committed |
| CORS | Allow-list via `CORS_ORIGINS` |
| Input validation | Pydantic v2 strict typing |
| Webhook signing | HMAC-SHA256 on all alert webhook deliveries |
| Logs | No PII; secrets masked at boundary |
| Container | Non-root user, read-only FS, minimal Alpine images |
| Dependencies | Dependabot weekly + `pip-audit` + `npm audit --audit-level=high` in CI |

## 7. Observability Stack

```
Application
  ├── Traces    → OpenTelemetry SDK → OTLP → Azure Monitor / Jaeger
  ├── Metrics   → OpenTelemetry SDK → OTLP
  │             → prometheus_client (/metrics) → Prometheus / Grafana
  └── Logs      → structlog JSON → stdout → Loki / Azure Log Analytics
```

W3C TraceContext is propagated browser → backend → downstream LLM/Ollama via auto-instrumented `httpx` client.

## 8. Failure Modes & Mitigations

| Failure | Mitigation |
|---------|-----------|
| Backend down | Frontend renders `ErrorCard` per query; SPA still routes |
| Ollama unreachable | `/api/v1/llm/runtime` returns structured `reachable=false` |
| OTel collector down | Batch span processor buffers; logs continue to stdout |
| Cost source missing | Service returns deterministic stub data (dev-friendly) |
| Excess load | HPA scales replicas; Prometheus histogram surfaces tail latency |
