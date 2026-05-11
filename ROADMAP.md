# Roadmap — Vectaris

A phased plan from the current MVP toward an enterprise-grade AI observability platform.

> **Current version: v1.5-alpha** (May 11, 2026)
> Phases 0–4 shipped. Phase 5 in progress (OIDC + rate-limiting done; DB, RBAC, audit log pending).
> See [PHASES.md](PHASES.md) for full deliverables, acceptance criteria, and effort estimates.

---

## Implementation Priority — Next Actions

> Work the phases in this order. Each block is a shippable increment.

### 🔴 P1 — Phase 5 core (blocks everything downstream)
1. Add PostgreSQL + Redis to `docker-compose.yml` and update `backend/.env.example`
2. Add `sqlalchemy[asyncio]`, `asyncpg`, `alembic` to `requirements.txt`
3. Create `backend/app/db/` package — `base.py`, `session.py`, ORM models for agents / alerts / costs / tenants / audit
4. Run `alembic init` + generate initial migration; add `scripts/db-migrate.sh`
5. Migrate all in-memory services to async SQLAlchemy (`agent_service`, `alert_rules_service`, `cost_service`)
6. Add tenant URL scoping (`/t/{tenant_id}/api/v1/...`) + 301 redirect for `/api/v1/...`
7. Add RBAC (`require_role` dependency) — Admin / Operator / Viewer / Billing
8. Add `AuditMiddleware` + `GET /admin/audit` endpoint
9. Update tests: `conftest.py` with SQLite in-memory fixtures; migrate existing 19 tests to `httpx.AsyncClient`

### 🟠 P2 — Phase 3.1 & 4.1 (parallel streams, depend on P1 DB layer)
10. `notification_channels` table + CRUD API; Slack / Teams / PagerDuty / email / webhook implementations
11. Alert deduplication (`dedup_key`) + flapping suppression (`flap_count`, cooldown)
12. SLO definitions table + burn-rate alert evaluation + Dashboard gauge widget
13. ARIMA / Prophet forecast model selection (`?model=arima`) via `statsmodels`
14. Team budgets table + Z-score anomaly detection; anomaly markers on Cost chart
15. `POST /api/v1/costs/simulate` what-if endpoint + `GET /api/v1/costs/export?format=csv`

### 🟡 P3 — Phase 6 Agent Orchestration (depends on P1 + P2)
16. Add OTLP ingest endpoint + `agent_runs` / `agent_run_spans` DB tables
17. Python SDK packages: `vectaris-core`, `vectaris-langchain`, `vectaris-autogen` under `sdk/`
18. Agent Run Timeline page (`/agents/:id/runs`) with `TraceWaterfall` component
19. Reliability scorecards — MTTR, drift detector, P99 trend — per-agent panel on Agents page
20. Replay-from-trace — `POST /api/v1/agents/{id}/replay` + UI diff view

### 🔵 CI/CD (parallel throughout all phases)
- Add `db-migration-check`, `backend-coverage` (≥80%), `sast` (bandit + eslint-security) jobs to CI
- Multi-stage Dockerfiles (non-root `USER 1000`); push to `ghcr.io` on `main`
- `staging-deploy` job on `main` merge; `production-deploy` via manual `workflow_dispatch`
- New scripts: `setup-dev.sh`, `seed.sh`, `test-all.sh`, `publish-sdk.sh`

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
- [ ] Persistent storage layer (PostgreSQL via SQLAlchemy 2.x async) — _Phase 5, P1 next_

---

## Phase 2 — Multi-Provider LLM Support (shipped · v1.2)

**Goal:** unify cost/latency telemetry across LLM providers.

- [x] LLM proxy endpoint (`POST /api/v1/llm/chat`) with token + latency capture
- [x] OTel context propagation through LLM proxy (W3C traceparent)
- [x] Distributed tracing demo (`examples/tracing-demo/`) — mock OpenAI + Ollama
- [x] GraphQL gateway alongside REST (Strawberry at `/graphql`, GraphiQL IDE)
- [ ] Full provider plugin interface (`Provider` protocol) — _deferred to post-v2.0_
- [ ] Token-usage analytics dashboard with model comparison — _deferred to post-v2.0_
- [ ] vLLM / Bedrock built-in plugins — _deferred to post-v2.0_

---

## Phase 3 — Alerting & Notifications (shipped · v1.3)

- [x] YAML-defined alert rules with CRUD API (`GET/PUT/DELETE /api/v1/alerts/rules/{id}`)
- [x] Background scheduler (APScheduler) for periodic evaluation + webhook delivery
- [x] Webhook signing (HMAC-SHA256) + retry
- [x] Toast notifications in UI for new critical alerts
- [ ] Notification channels: Slack, Teams, PagerDuty, email — _Phase 3.1, P2_
- [ ] Alert deduplication + flapping suppression (`dedup_key`, cooldown, flap_count) — _Phase 3.1, P2_
- [ ] SLO tracking + burn-rate alerts + Dashboard gauge — _Phase 3.1, P2_

---

## Phase 4 — Cost Forecasting & FinOps (shipped · v1.4)

- [x] Linear cost forecast with horizon picker (7 / 30 / 60 / 90 days)
- [x] Per-model and per-team cost breakdown
- [x] Azure Cost Management + AWS CUR adapters
- [ ] Time-series cost persistence in `cost_records` table — _Phase 5 DB layer, P1_
- [ ] ARIMA / Prophet forecast model (`?model=arima` via `statsmodels`) — _Phase 4.1, P2_
- [ ] Per-team budgets (`team_budgets` table) + Z-score anomaly detection — _Phase 4.1, P2_
- [ ] "What-if" simulator (`POST /api/v1/costs/simulate`) — _Phase 4.2, P2_
- [ ] Showback / chargeback CSV export (`GET /api/v1/costs/export?format=csv`) — _Phase 4.2, P2_

---

## Phase 5 — Multi-Tenant & RBAC (in progress · v1.5)

> **Status:** OIDC and rate-limiting shipped. DB, RBAC, audit log — not yet started.
> **Blocking:** all Phase 3.1, 4.1, 4.2, and 6 work depends on the DB layer.

- [x] OIDC integration (Azure AD, Okta, Auth0 via PyJWKClient)
- [x] Per-tenant rate limiting and monthly token quotas (slowapi)
- [ ] **[P1-1]** PostgreSQL 16 + Redis in `docker-compose.yml`; `sqlalchemy[asyncio]`, `asyncpg`, `alembic` in `requirements.txt`
- [ ] **[P1-2]** `backend/app/db/` package — `base.py`, `session.py`, ORM models for agents / alert_rules / alert_events / cost_records / metrics_snapshots / tenants / audit_log
- [ ] **[P1-3]** Alembic init + initial migration; `scripts/db-migrate.sh` + `scripts/db-rollback.sh`
- [ ] **[P1-4]** Migrate `agent_service`, `alert_rules_service`, `cost_service` to async SQLAlchemy; router handlers → `async def`
- [ ] **[P1-5]** Tenant URL scoping (`/t/{tenant_id}/api/v1/...`); 301 redirect from `/api/v1/...`; `POST/GET /admin/tenants`
- [ ] **[P1-6]** RBAC — `require_role(Role.*)` FastAPI dependency; `vectaris_role` JWT claim; roles wired to each router verb
- [ ] **[P1-7]** `AuditMiddleware` (SHA-256 body hash, no raw payload); `GET /admin/audit` paginated, Admin-only
- [ ] **[P1-8]** Test suite — `conftest.py` SQLite in-memory fixtures; 19 existing tests migrated to `httpx.AsyncClient`; 5+ new DB-layer tests; `--cov-fail-under=80` CI gate

---

## Phase 3.1 — Notifications & SLO Tracking (planned · v1.6)

> **Depends on:** Phase 5 DB layer. Can be developed in parallel with Phase 4.1.

- [ ] **[P2-1]** `notification_channels` table (config JSONB encrypted with Fernet) + `GET/POST/DELETE /api/v1/alerts/channels`
- [ ] **[P2-2]** Slack (Block Kit), Teams (Adaptive Card), PagerDuty (Events API v2), email (`aiosmtplib` + Jinja2) implementations
- [ ] **[P2-3]** Webhook retry: exponential backoff (3 attempts) + dead-letter row in `alert_events`
- [ ] **[P2-4]** Alert deduplication — `dedup_key = f"{rule_id}:{entity_id}"`, 15-min cooldown window configurable per rule
- [ ] **[P2-5]** Flapping suppression — tag `FLAPPING` when alert fires+clears >3× in 10 min; suppress notifications
- [ ] **[P2-6]** `slo_definitions` table + `slo_service.evaluate_slo()` + burn-rate alert + APScheduler job (300s)
- [ ] **[P2-7]** `GET/POST /api/v1/slo` + `GET /api/v1/slo/{id}/status` endpoints
- [ ] **[P2-8]** Frontend: SLO compliance gauge + error budget bar on `DashboardPage` (Recharts)

---

## Phase 4.1 & 4.2 — Advanced FinOps (planned · v1.6)

> **Depends on:** Phase 5 DB layer (`cost_records` table). Can be developed in parallel with Phase 3.1.

- [ ] **[P2-9]** ARIMA forecast via `statsmodels.tsa.arima.model.ARIMA`; Prophet as optional extra; `?model=arima` query param
- [ ] **[P2-10]** `team_budgets` table + `GET/POST/PUT /api/v1/costs/budgets`
- [ ] **[P2-11]** Z-score anomaly detection over 7-day rolling window; `anomaly: bool` field in cost history; red dot markers on `CostBreakdown`
- [ ] **[P2-12]** `POST /api/v1/costs/simulate` — body: `{model_swap, token_reduction_pct, rate_change_pct, horizon_days}`; returns delta forecast
- [ ] **[P2-13]** `GET /api/v1/costs/export?format=csv&from=&to=&team=` — `StreamingResponse` with `text/csv`
- [ ] **[P2-14]** Frontend: "Export CSV" button + "Run Simulation" slider panel on `CostsPage`

---

## Phase 6 — Agent Orchestration & Reliability (planned · v2.0)

> **Depends on:** Phase 5 DB layer (agent_runs / agent_run_spans tables).

- [ ] **[P3-1]** OTLP HTTP ingest (`POST /v1/traces`) + `agent_runs` / `agent_run_spans` ORM models + `GET /api/v1/agents/{id}/runs` + `GET /api/v1/runs/{run_id}/spans`
- [ ] **[P3-2]** Python SDK packages under `sdk/` — `vectaris-core` (client), `vectaris-langchain` (callback tracer), `vectaris-autogen` (middleware); published to PyPI
- [ ] **[P3-3]** Agent Run Timeline page (`/agents/:id/runs`) with `TraceWaterfall` component (span bars proportional to duration, color-coded by kind)
- [ ] **[P3-4]** Reliability scorecards — `reliability_service.py` (MTTR, 7-day success-rate trend, drift detector >10% WoW, P99 >2× baseline); `GET /api/v1/agents/{id}/scorecard`; collapsible panel on Agents page
- [ ] **[P3-5]** Replay-from-trace — `agent_run_inputs` table (encrypted, opt-in); `POST /api/v1/agents/{id}/replay`; diff view on Timeline UI

---

## Phase 7 — Edge Telemetry & Browser SDK (planned · v2.1)

- [x] OTel Browser SDK + Web Vitals integration (`src/telemetry.ts`)
- [x] PWA manifest + service worker offline cache
- [ ] `@vectaris/browser-sdk` npm package (standalone, publishable) — _post-Phase 6_
- [ ] Real-user monitoring panel — _post-Phase 6_

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
