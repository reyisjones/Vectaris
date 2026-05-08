# Roadmap — Vectaris

A phased plan from the current MVP toward an enterprise-grade AI observability platform.

> **Current version: v1.5-alpha** (May 2026)
> All Phase 0–2 work is shipped. Phases 3–5 are partially complete.
> See [PHASES.md](PHASES.md) for the detailed next-phase planning document.

---

## Phase 0 — MVP (shipped · v1.0)

- [x] FastAPI backend with usage / latency / agents / costs / alerts / LLM runtime
- [x] React 18 SPA with Dashboard, Agents, Costs, Alerts, LLM pages
- [x] OpenTelemetry tracing + metrics scaffolding
- [x] Prometheus `/metrics` endpoint + per-request HTTP histogram
- [x] Structured JSON logging with request-ID correlation
- [x] Live alert evaluation (latency / error-rate / agent thresholds)
- [x] Ollama runtime status endpoint
- [x] Docker Compose, Kubernetes manifests, GitHub Actions CI
- [x] MIT license, comprehensive docs

---

## Phase 1 — Real Data Sources (shipped · v1.1)

**Goal:** replace stub services with live integrations.

- [x] Azure Monitor + Application Insights query adapter
- [x] PromQL / Prometheus federation adapter
- [x] OpenAI / Azure OpenAI usage + billing import
- [x] AWS CUR cost adapter (SigV4 signed, no boto3)
- [x] Agent self-registration endpoint (`POST /api/v1/agents`)
- [x] API key authentication middleware (`X-API-Key`)
- [x] OIDC / Azure Managed Identity (Azure AD, Okta, Auth0 via PyJWKClient)
- [ ] Persistent storage layer (PostgreSQL via SQLAlchemy 2.x async) — _deferred to Phase 5_

---

## Phase 2 — Multi-Provider LLM Support (shipped · v1.2)

**Goal:** unify cost/latency telemetry across LLM providers.

- [x] LLM proxy endpoint (`POST /api/v1/llm/chat`) with token + latency capture
- [x] OTel context propagation through LLM proxy (W3C traceparent)
- [x] Distributed tracing demo (`examples/tracing-demo/`) — mock OpenAI + Ollama
- [x] GraphQL gateway alongside REST (Strawberry at `/graphql`, GraphiQL IDE)
- [ ] Full provider plugin interface (`Provider` protocol) — _deferred_
- [ ] Token-usage analytics dashboard with model comparison — _deferred_
- [ ] vLLM / Bedrock built-in plugins — _deferred_

---

## Phase 3 — Alerting & Notifications (shipped · v1.3)

- [x] YAML-defined alert rules with CRUD API (`GET/PUT/DELETE /api/v1/alerts/rules/{id}`)
- [x] Background scheduler (APScheduler) for periodic evaluation + webhook delivery
- [x] Webhook signing (HMAC-SHA256) + retry
- [x] Toast notifications in UI for new critical alerts
- [ ] Notification channels: Slack, Teams, PagerDuty, email — _planned Phase 3.1_
- [ ] Alert deduplication + flapping suppression — _planned Phase 3.1_
- [ ] SLO tracking with burn-rate alerts — _planned Phase 3.2_

---

## Phase 4 — Cost Forecasting & FinOps (shipped · v1.4)

- [x] Linear cost forecast with horizon picker (7 / 30 / 60 / 90 days)
- [x] Per-model and per-team cost breakdown
- [x] Azure Cost Management + AWS CUR adapters
- [ ] Time-series cost persistence — _planned Phase 5 (DB layer)_
- [ ] ARIMA / Prophet forecast option — _planned Phase 4.1_
- [ ] Per-team budgets with anomaly detection — _planned Phase 4.1_
- [ ] "What-if" simulator — _planned Phase 4.2_
- [ ] Showback / chargeback CSV export — _planned Phase 4.2_

---

## Phase 5 — Multi-Tenant & RBAC (in progress · v1.5)

- [x] OIDC integration (Azure AD, Okta, Auth0)
- [x] Per-tenant rate limiting and monthly token quotas (slowapi)
- [ ] Persistent storage layer (PostgreSQL + SQLAlchemy 2.x async) — _next_
- [ ] Tenant URL scoping (`/t/{tenant}/api/v1/...`) — _next_
- [ ] RBAC roles: Admin, Operator, Viewer, Billing — _next_
- [ ] Audit log of mutating actions — _next_

---

## Phase 6 — Agent Orchestration & Reliability (planned · v2.0)

- [ ] LangGraph / CrewAI / AutoGen integration adapters
- [ ] Agent run timeline with span tree visualization
- [ ] Reliability scorecards (MTTR, success-rate trend, drift detector)
- [ ] Replay-from-trace developer tool

---

## Phase 7 — Edge Telemetry & Browser SDK (planned · v2.1)

- [x] OTel Browser SDK + Web Vitals integration (`src/telemetry.ts`)
- [x] PWA manifest + service worker offline cache
- [ ] `@vectaris/browser-sdk` npm package (standalone, publishable)
- [ ] Real-user monitoring panel

---

## Phase 8 — Distributed Tracing UI (planned · v2.2)

- [ ] Built-in trace explorer (no Jaeger required)
- [ ] Service map auto-derived from spans
- [ ] Critical-path analysis for agent runs

---

## Phase 9 — Kubernetes / Infra Telemetry (planned · v2.3)

- [x] ServiceMonitor + PrometheusRule CRDs shipped
- [x] Grafana dashboard JSON provisioned
- [ ] Node / pod resource correlation with AI workloads
- [ ] GPU utilization (DCGM exporter integration)

---

## Phase 10 — Hosted Offering (planned · v3.0)

- [ ] Managed multi-tenant SaaS deployment
- [ ] Organization billing portal
- [ ] Marketplace of provider plugins + alert templates
