# Sample GitHub Issues — ai-platform-dashboard

> Paste each item as a GitHub issue after creating the repo.

---

**Issue #1: Set up FastAPI project structure with Pydantic v2 schemas**
- Labels: `enhancement`, `backend`
- Body: Scaffold `backend/app/` with routers, models, services, and telemetry directories. Add main.py app factory with CORS and lifespan hooks.

---

**Issue #2: Implement `/api/v1/metrics/usage` and `/api/v1/metrics/latency` endpoints**
- Labels: `enhancement`, `backend`
- Body: Return usage aggregates (requests, tokens, errors) and latency percentiles (P50/P95/P99) per model. Use stub data initially.

---

**Issue #3: Add OpenTelemetry tracing and Prometheus metrics endpoint**
- Labels: `observability`, `backend`
- Body: Configure OTel TracerProvider with OTLP exporter. Instrument FastAPI with `FastAPIInstrumentor`. Expose `/metrics` for Prometheus scraping.

---

**Issue #4: Scaffold React frontend with Vite + TypeScript**
- Labels: `enhancement`, `frontend`
- Body: Create Vite + React 18 + TypeScript project. Add TanStack Query for data fetching and Recharts for visualizations. Configure dev proxy to backend.

---

**Issue #5: Build DashboardPage with KPI cards (requests, tokens, cost, errors)**
- Labels: `enhancement`, `frontend`
- Body: Implement `MetricCard` component. Compose `DashboardPage` with KPI row, latency chart, and agent health table. Poll every 30s.

---

**Issue #6: Build LatencyChart component (P50/P95/P99 line chart)**
- Labels: `enhancement`, `frontend`
- Body: Use Recharts `LineChart`. Show three lines per model. Dark theme matching dashboard.

---

**Issue #7: Add Docker Compose for local development**
- Labels: `devops`, `infrastructure`
- Body: Create `docker-compose.yml` with `backend` and `frontend` services. Add healthcheck on backend before frontend starts.

---

**Issue #8: Add GitHub Actions CI — lint, test, Docker build**
- Labels: `ci/cd`
- Body: Add `ci.yml` with three jobs: backend lint+test (ruff, mypy, pytest), frontend lint (eslint), and docker build for both images.

---

**Issue #9: Create Kubernetes manifests (Deployment, Service, HPA)**
- Labels: `infrastructure`, `kubernetes`
- Body: Add `deploy/kubernetes/` with namespace, backend deployment (non-root, resource limits, liveness/readiness probes), service, and HPA (min 2, max 10 replicas).

---

**Issue #10: Add Azure Container Apps Bicep deployment template**
- Labels: `infrastructure`, `azure`
- Body: Create `deploy/azure/main.bicep` with Container App Environment, backend Container App, and ACR integration. Add `parameters.json` for environment-specific values.
