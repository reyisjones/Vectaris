# Cleanup Report

Summary of issues detected and fixes applied during the full project audit.

---

## Build & Tooling Fixes

| # | Issue | Fix |
|---|-------|-----|
| 1 | Missing `frontend/tsconfig.json` and `tsconfig.node.json` — `npm run build` (`tsc && vite build`) would fail | Added strict TS config + Node-side config |
| 2 | Missing ESLint config — `npm run lint` would fail | Added `.eslintrc.cjs` with TS + react-hooks plugins |
| 3 | Missing `src/vite-env.d.ts` — `import.meta.env` typed as `any` | Added Vite env types declaration |
| 4 | `frontend/Dockerfile` exposed port 3000 but nginx serves on 80 (compose maps `3000:80`) | Fixed `EXPOSE 80`, added `nginx.conf` with SPA fallback |
| 5 | Missing `frontend/nginx.conf` — client-side routes (`/agents`, `/costs`…) returned 404 on refresh | Added SPA fallback `try_files $uri $uri/ /index.html` |
| 6 | CI workflow used `npm ci` without committed lockfile | Switched to `npm install` and added build step |
| 7 | Missing `LICENSE` file referenced in README | Added MIT LICENSE |
| 8 | Missing `.gitignore` | Added Python + Node + IDE entries |

---

## Backend Code Quality

| # | Issue | Fix |
|---|-------|-----|
| 1 | `routers/health.py` returned `PlainTextResponse` from a function typed `-> str` — type lie | Returns `Response` with explicit `media_type` |
| 2 | CORS `allow_methods=["GET"]` blocked future POST endpoints | Allow `GET, POST, OPTIONS` and a configurable origins list |
| 3 | OTel setup wired only traces, no metrics; instrumentation called inside lifespan with no app handle | Split into `configure_telemetry()` + `instrument_app(app)`; added `MeterProvider` + `httpx` instrumentation |
| 4 | No request correlation — logs unjoinable to traces | Added `RequestContextMiddleware` with `X-Request-ID`, structlog ctxvars, and trace_id injection |
| 5 | No structured logging — only default uvicorn output | Added `logging_config.py` with structlog JSON renderer |
| 6 | No HTTP-level Prometheus instrumentation | Added `http_requests_total` counter and `http_request_duration_seconds` histogram |
| 7 | Alerts router returned static seeded data — not derived from telemetry | New `alert_service.evaluate_alerts()` evaluates latency / error-rate / agent-success-rate against thresholds |
| 8 | Cost service had hard-coded duplicated `by_team` rows | `_aggregate_by_team()` derives team totals from records |
| 9 | No cost forecasting endpoint | Added `/api/v1/costs/forecast` with linear projection |
| 10 | No LLM runtime visibility | New `llm_runtime_service` (Ollama integration) + `/api/v1/llm/runtime` endpoint |
| 11 | Missing `/ready` endpoint for K8s readiness probe | Added |
| 12 | Pydantic models used `X | None = None` syntax that breaks on Python < 3.10 | Switched model fields to `Optional[X]` for Pydantic-build-time eval safety |
| 13 | `Settings` accepted `extra="ignore"` only — no encoding declared | Added `env_file_encoding="utf-8"` and richer fields (`api_version`, `cors_origins`, `request_timeout_seconds`, ollama settings) |

---

## Frontend Code Quality

| # | Issue | Fix |
|---|-------|-----|
| 1 | Single-page app despite README/Architecture mentioning multiple pages | Added React Router v6, 5 pages (Dashboard / Agents / Costs / Alerts / LLM) |
| 2 | Inline styles everywhere → unmaintainable, no theme tokens | Added `styles/global.css` with CSS variables, refactored components to use `card`, `badge`, `grid` utility classes |
| 3 | No global navigation | Added `AppLayout` sidebar with NavLink active states, responsive breakpoint |
| 4 | No loading or error states | Added `LoadingCard` skeleton + `ErrorCard`; queries surface them |
| 5 | `LatencyChart` was a line chart over a categorical axis — visually meaningless | Switched to grouped BarChart per model |
| 6 | Type for `Agent.status` duplicated in two places | Centralized `AgentStatus` type in `services/api.ts` |
| 7 | API client missing endpoints (`/llm/runtime`, `/costs/forecast`, agent health) | Added typed callers |
| 8 | No alerts UI element on dashboard beyond a count | Added `AlertsList` widget showing severity, message, source, time |
| 9 | No cost visualizations on Costs page | Added `CostBreakdown` BarChart for model and team |
| 10 | `react-router-dom` not in `package.json` | Added dependency |

---

## Tests

- 13 backend tests passing (was 8): added `/ready`, `/metrics`, request-ID round-trip, cost forecast, agent-not-found assertion strengthened, alert-shape assertion, LLM runtime disabled-by-default behaviour.

```
$ pytest backend/tests -q
.............                                                            [100%]
13 passed in 0.17s
```

---

## Architecture / Modularity Improvements

- Telemetry split into idempotent `configure_telemetry()` + `instrument_app()`.
- Routers stay thin; all logic in `app/services/*` (single-responsibility).
- Configuration centralised in `app/config.py` (no scattered `os.getenv`).
- Logging wired once in `configure_logging()`; called both from `create_app()` and `lifespan` to handle `TestClient` (which skips lifespan in some flows).
- Frontend structured by **layer**: shell → pages → widgets → data, with shared theme tokens.

---

## Documentation Refresh

- `README.md` — fully rewritten with capability list, full env table, current API surface, project tree.
- `ARCHITECTURE.md` — system diagrams, data flow, request lifecycle, security, observability, failure modes.
- `ROADMAP.md` — 10 phases from MVP to hosted SaaS.
- `TODO.md` — prioritised P0/P1/P2 backlog across backend, frontend, telemetry, infra, docs.
- This `CLEANUP_REPORT.md`.

---

## Files Added

```
ARCHITECTURE.md
CLEANUP_REPORT.md
LICENSE
README.md (rewritten)
ROADMAP.md
TODO.md
.gitignore
backend/app/logging_config.py
backend/app/middleware.py
backend/app/models/alert.py
backend/app/models/llm.py
backend/app/services/alert_service.py
backend/app/services/llm_runtime_service.py
backend/app/routers/llm.py
frontend/.eslintrc.cjs
frontend/nginx.conf
frontend/tsconfig.json
frontend/tsconfig.node.json
frontend/src/vite-env.d.ts
frontend/src/styles/global.css
frontend/src/components/AppLayout.tsx
frontend/src/components/AlertsList.tsx
frontend/src/components/CostBreakdown.tsx
frontend/src/components/LLMRuntimeCard.tsx
frontend/src/components/LoadingState.tsx
frontend/src/components/PageHeader.tsx
frontend/src/pages/AgentsPage.tsx
frontend/src/pages/AlertsPage.tsx
frontend/src/pages/CostsPage.tsx
frontend/src/pages/LLMRuntimePage.tsx
```

## Files Modified

```
backend/.env.example
backend/app/config.py
backend/app/main.py
backend/app/models/cost.py
backend/app/routers/alerts.py
backend/app/routers/costs.py
backend/app/routers/health.py
backend/app/services/agent_service.py
backend/app/services/cost_service.py
backend/app/telemetry/setup.py
backend/tests/test_api.py
frontend/Dockerfile
frontend/package.json
frontend/src/App.tsx
frontend/src/main.tsx
frontend/src/components/AgentHealthTable.tsx
frontend/src/components/LatencyChart.tsx
frontend/src/components/MetricCard.tsx
frontend/src/pages/DashboardPage.tsx
frontend/src/services/api.ts
.github/workflows/ci.yml
```
