# Next Project Phases — Vectaris

> **Date:** May 11, 2026 · **Current state:** v1.5-alpha
>
> All P0–P2 backlog items are complete. This document defines the three next meaningful phases with
> concrete deliverables, acceptance criteria, and effort estimates.
>
> See [ROADMAP.md](ROADMAP.md) for the high-level phase overview and prioritised next-action list.

---

## Status Overview

| Phase | Scope | Status | Blocks |
|-------|-------|--------|--------|
| **5.1** | Persistent Storage (PostgreSQL + Alembic) | 🔲 Not started | Everything below |
| **5.2** | Tenant URL Scoping | 🔲 Not started | 5.3, 5.4 |
| **5.3** | RBAC Roles | 🔲 Not started | 5.4 |
| **5.4** | Audit Log | 🔲 Not started | — |
| **3.1** | Notification Channels (Slack / Teams / PD / Email) | 🔲 Not started | — |
| **3.1** | Alert Deduplication + Flapping Suppression | 🔲 Not started | — |
| **3.1** | SLO Tracking + Burn-rate Alerts | 🔲 Not started | — |
| **4.1** | ARIMA / Prophet Forecast Model | 🔲 Not started | — |
| **4.1** | Team Budgets + Anomaly Detection | 🔲 Not started | — |
| **4.2** | What-if Simulator + CSV Export | 🔲 Not started | — |
| **6.1** | Agent Framework Adapters (SDK packages) | 🔲 Not started | Phase 5 DB |
| **6.2** | Agent Run Timeline UI | 🔲 Not started | Phase 5 DB |
| **6.3** | Reliability Scorecards | 🔲 Not started | Phase 5 DB |
| **6.4** | Replay-from-Trace | 🔲 Not started | 6.1, 6.2 |

---

## Sprint 1 — Phase 5.1: Persistent Storage Layer (🔲 Not started)

> **Priority:** P1 — must ship before any other open item.
> **Estimated effort:** 2 sprints (3–4 weeks)

### Implementation steps in order:

1. **`docker-compose.yml`** — add `postgres:16-alpine` (healthcheck `pg_isready`) and `redis:7-alpine` services; add `pgdata` named volume; wire `backend` `depends_on: postgres: condition: service_healthy`; add `DATABASE_URL` and `REDIS_URL` to backend env.
2. **`backend/requirements.txt`** — add `sqlalchemy[asyncio]>=2.0.30`, `asyncpg>=0.29.0`, `alembic>=1.13.0`, `aiosmtplib>=3.0.0`, `jinja2>=3.1.4`, `statsmodels>=0.14.2`. Add `aiosqlite>=0.20.0` to `requirements-dev.txt`.
3. **`backend/app/config.py`** — add `database_url: str = ""`, `secret_key: str = ""` (Fernet), SMTP settings.
4. **`backend/app/db/`** — create package:
   - `base.py`: `DeclarativeBase` subclass `Base`; `TimestampMixin(created_at, updated_at)`
   - `session.py`: `AsyncSessionLocal = async_sessionmaker(...)`; `get_db()` dependency; `init_db()` called at startup
   - `db/models/tenant.py`, `agent.py`, `alert_rule.py`, `alert_event.py`, `cost_record.py`, `metrics_snapshot.py`, `audit_log.py`
5. **`backend/alembic/`** — `alembic init backend/alembic`; configure `env.py` to use `settings.database_url` + `Base.metadata`; generate initial migration `alembic revision --autogenerate -m "initial schema"`.
6. **`scripts/db-migrate.sh`** + **`scripts/db-rollback.sh`** — venv-aware wrappers for `alembic upgrade head` / `alembic downgrade -1`.
7. **Migrate services** — replace in-memory dicts/lists in `agent_service.py`, `alert_rules_service.py`, `alert_service.py`, `cost_service.py` with `AsyncSession` queries; all service functions become `async def`; inject `db: AsyncSession = Depends(get_db)` in routers; router handlers become `async def`.
8. **Update `backend/app/main.py`** — call `await init_db()` in lifespan startup; update docker-compose backend `command` to run `alembic upgrade head` before uvicorn.
9. **`backend/tests/conftest.py`** — `async_engine` fixture (SQLite in-memory via `aiosqlite`); `test_db` fixture (creates tables, yields `AsyncSession`, rolls back after each test); override `get_db` FastAPI dependency; migrate existing 19 tests to `httpx.AsyncClient`; add 5+ DB-layer tests (persist → new session → reload).

**Acceptance criteria:**
- `alembic upgrade head` then `alembic downgrade -1` on a fresh PostgreSQL 16 instance
- Server restart with PostgreSQL running: registered agents persist across restarts
- All 19+ backend tests pass; ≥5 new DB-layer tests added; `pytest --cov-fail-under=80` passes
- `docker-compose up` brings up postgres + redis before backend starts

---

---

## Phase 5 Completion — Persistence, Multi-Tenancy & RBAC (v1.5)

**Goal:** graduate from in-memory state to a real database; lock down every API surface with tenant scoping and role-based access control.

### 5.1 — Persistent Storage Layer 🔲

| Item | Detail |
|------|--------|
| Database | PostgreSQL 16 via SQLAlchemy 2.x async (`asyncpg` driver) |
| Migrations | Alembic with auto-generated revision files |
| Agent registry | Persist `POST /api/v1/agents` registrations across restarts |
| Metrics history | Rolling 90-day store of usage + latency samples (time-series table) |
| Alert rules | Migrate from in-memory dict to `alert_rules` table |
| Alert history | Persist evaluated alert events for audit and trend views |
| Cost records | Time-stamped cost records per model + team |
| Local dev | PostgreSQL service added to `docker-compose.yml`; `DATABASE_URL` env var |
| Tests | SQLite in-memory for unit tests; `pytest-asyncio` + `httpx.AsyncClient` |

**Acceptance criteria:**
- Server restart preserves agents, alert rules, and cost history
- `alembic upgrade head` applies all migrations cleanly against a fresh PostgreSQL instance
- All existing 19 backend tests continue to pass; 5+ new DB-layer tests added

---

### 5.2 — Tenant URL Scoping 🔲

| Item | Detail |
|------|--------|
| URL prefix | All v1 routes move under `/t/{tenant_id}/api/v1/...` |
| Backward compat | `/api/v1/...` redirects to `/t/default/api/v1/...` (301) |
| Data isolation | Every DB query scoped by `tenant_id` extracted from JWT `tid` claim or `X-Tenant-ID` header |
| Tenant table | `tenants(id, name, plan, token_quota_monthly, created_at)` |
| Admin endpoint | `POST/GET /admin/tenants` for tenant provisioning (Admin role only) |

---

### 5.3 — RBAC Roles 🔲

| Role | Permissions |
|------|-------------|
| `Admin` | All actions including tenant management, user provisioning |
| `Operator` | Read + write agents, alert rules, LLM proxy; read metrics/costs |
| `Viewer` | Read-only across all resources |
| `Billing` | Read costs and quotas only |

Implementation:
- Role stored as a claim in the JWT (`vectaris_role`) or in `user_roles` table
- `require_role(Role.OPERATOR)` FastAPI dependency injected at router level
- GraphQL resolvers apply same role checks via context

---

### 5.4 — Audit Log 🔲

- `audit_log(id, tenant_id, user_id, action, resource_type, resource_id, payload_hash, timestamp)` table
- Every mutating API call (POST / PUT / PATCH / DELETE) writes an audit entry
- `GET /admin/audit?from=&to=&user=&resource=` query endpoint (Admin only)
- Log entries are append-only; no DELETE endpoint

---

**Estimated effort:** 3–4 sprints (6–8 weeks)

---

## Phase 3.1 & 4.1 — Notifications + Advanced FinOps (v1.6)

These two streams can be developed in parallel by separate contributors. Both depend on the Phase 5 DB layer.

### 3.1 — Notification Channels 🔲

| Channel | Implementation |
|---------|----------------|
| Slack | Incoming webhook via `httpx`; block-kit formatted message |
| Microsoft Teams | Adaptive Card via Teams webhook URL |
| PagerDuty | Events API v2; severity mapping from alert level |
| Email (SMTP) | `aiosmtplib`; Jinja2 HTML template |
| Webhook (existing) | Extended with retry backoff + dead-letter queue (in-DB) |

Config stored in `notification_channels` table; managed via `GET/POST/DELETE /api/v1/alerts/channels`.

**Alert deduplication + flapping suppression:**
- Dedup key: `(rule_id, affected_entity)` — suppress duplicate fire within a cooldown window (configurable, default 15 min)
- Flapping: if an alert fires and clears more than 3× within 10 min, suppress and tag as `FLAPPING`

**SLO tracking:**
- `slo_definitions(id, tenant_id, name, target_pct, window_days, metric_query)` table
- Burn-rate alert: fires when error budget will be exhausted in < `burn_rate_factor × window` hours
- Dashboard widget: SLO compliance gauge + remaining error budget bar

---

### 4.1 — Advanced Cost Forecasting 🔲

| Item | Detail |
|------|--------|
| Model options | Linear (existing) · ARIMA (via `statsmodels`) · Prophet (via `prophet`) |
| Selection | `?model=arima` query param on `/api/v1/costs/forecast` |
| Per-team budgets | `team_budgets(tenant_id, team, monthly_usd_limit)` table; `GET /api/v1/costs/budgets` |
| Anomaly detection | Z-score over 7-day rolling window; anomalies surfaced in cost history response |
| What-if simulator | `POST /api/v1/costs/simulate` — accepts model swap, token reduction %, rate change; returns delta forecast |
| Export | `GET /api/v1/costs/export?format=csv&from=&to=` for showback / chargeback |

---

**Estimated effort:** 2–3 sprints (4–6 weeks) per stream

---

## Phase 6 — Agent Orchestration & Reliability (v2.0)

**Goal:** Vectaris becomes the reliability plane for multi-agent systems — not just a passive observer, but an active partner in debugging and stabilizing agent workflows.

> **Depends on:** Phase 5 DB layer (agents, agent_runs, agent_run_spans tables must exist).

### 6.1 — Agent Framework Adapters 🔲

| Framework | Integration approach |
|-----------|---------------------|
| LangGraph | Custom `LangGraphTracer` callback that emits spans to Vectaris OTLP endpoint |
| CrewAI | `CrewAIObserver` hook — maps agent/task/tool events to OTel spans |
| AutoGen | `AutoGenTelemetryMiddleware` wrapping `ConversableAgent.initiate_chat` |
| Generic | OTel SDK instrumentation (already documented in `docs/guides/instrumenting-custom-agents.md`) |

SDK packages published as:
- `vectaris-langchain` (Python, PyPI)
- `vectaris-autogen` (Python, PyPI)

### 6.2 — Agent Run Timeline UI 🔲

- New page: `/agents/:id/runs` — waterfall trace view per agent run
- Each run = one root OTel trace; child spans = tool calls, LLM calls, sub-agent invocations
- Click-through from `AgentHealthTable` to timeline
- Backend: `GET /api/v1/agents/{id}/runs?limit=50` returning trace summaries from OTLP store

### 6.3 — Reliability Scorecards 🔲

| Metric | Definition |
|--------|-----------|
| MTTR (Mean Time to Recovery) | Avg time from `status=DEGRADED` to `status=HEALTHY` |
| Success-rate trend | 7-day moving average of `success_rate` per agent |
| Drift detector | Alert if success rate drops > 10% week-over-week |
| P99 latency trend | 7-day rolling P99 per agent; alert if > 2× baseline |

Scorecard displayed on `AgentsPage` as a collapsible panel per agent.

### 6.4 — Replay-from-Trace 🔲

- `POST /api/v1/agents/{id}/replay` — accepts a `trace_id`; re-submits the original input payload to the agent
- Captured input/output stored in `agent_run_inputs` table (opt-in per agent, requires `capture_inputs=true` flag)
- UI: "Replay" button on run timeline; diff view between original and replayed output

---

**Estimated effort:** 4–5 sprints (8–10 weeks)

---

## Guiding Principles for All Phases

1. **No breaking changes to REST contracts** — new fields are additive; removed fields go through a deprecation header cycle first.
2. **Feature flags for every major capability** — all new features behind an env var / tenant config flag, defaulting to `false` in production.
3. **Test coverage gate** — PRs must maintain ≥ 80 % line coverage on new backend code; Vitest coverage report added to CI.
4. **Backward-compatible migrations only** — Alembic migrations must be reversible (`downgrade` implemented).
5. **Docs ship with code** — every new endpoint gets a docstring, an ADR if it changes architecture, and an update to the relevant guide.

---

## CI/CD Pipeline Additions (parallel with all phases)

| Job | Trigger | Description |
|-----|---------|-------------|
| `db-migration-check` | PR + push | Spin up `postgres:16` service container; run `upgrade head → downgrade -1 → upgrade head` |
| `backend-coverage` | PR + push | `pytest --cov=app --cov-report=xml --cov-fail-under=80`; upload to Codecov |
| `sast` | PR + push | `bandit -r backend/app/ -ll` (medium+); ESLint `eslint-plugin-security` on frontend |
| `helm-lint` | PR + push | `helm lint deploy/helm/vectaris/` + `helm template \| kubectl --dry-run=client apply -f -` |
| `docker-build-matrix` | PR + push | Parallel backend + frontend multi-stage builds; push to `ghcr.io` on `main` merge |
| `staging-deploy` | `main` merge | `helm upgrade --install` to `vectaris-staging` namespace; smoke test `curl /health` |
| `production-deploy` | `workflow_dispatch` | Manual approval via GitHub environment protection; Helm upgrade to `vectaris-prod` |

**Multi-stage Dockerfile rules:**
- `backend/Dockerfile`: `builder` stage installs deps; `runtime` stage copies artifacts only; `USER 1000` (non-root)
- `frontend/Dockerfile`: already multi-stage; update base to `node:20-alpine`

**New scripts:**

| Script | Purpose |
|--------|---------|
| `scripts/setup-dev.sh` | Full dev bootstrap: checks Docker / Python 3.12 / Node 20; copies `.env.example`; installs deps; starts postgres + redis; runs migrations |
| `scripts/db-migrate.sh` | Activates venv; runs `alembic upgrade head` |
| `scripts/db-rollback.sh` | Activates venv; runs `alembic downgrade -1` |
| `scripts/seed.sh` | Inserts default tenant, sample agents, alert rules via `curl` against running backend |
| `scripts/test-all.sh` | Runs `pytest` + `vitest` + `helm lint` in sequence; exits non-zero on any failure |
| `scripts/publish-sdk.sh` | `python -m build` + `twine upload` for all SDK packages under `sdk/` |
