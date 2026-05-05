# Roadmap — Vectaris

A phased plan from the current MVP toward an enterprise-grade AI observability platform.

---

## Phase 0 — MVP (current release · v1.0)

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

## Phase 1 — Real Data Sources (v1.1)

**Goal:** replace stub services with live integrations.

- Azure Monitor + Application Insights query adapter
- PromQL / Prometheus federation adapter
- OpenAI / Anthropic / Azure OpenAI usage + billing import
- Persistent storage layer (PostgreSQL via SQLAlchemy 2.x async)
- Agent self-registration endpoint (`POST /api/v1/agents`)
- API key authentication middleware

---

## Phase 2 — Multi-Provider LLM Support (v1.2)

**Goal:** unify cost/latency telemetry across LLM providers.

- Provider plugin interface (`Provider` protocol with `usage()`, `models()`, `cost()`)
- Built-in plugins: OpenAI, Anthropic, Azure OpenAI, Bedrock, Ollama, vLLM
- Token-usage analytics dashboard with model comparison
- Provider-aware request proxy (capture latency at the proxy)

---

## Phase 3 — Alerting & Notifications (v1.3)

- YAML-defined alert rules with templating
- Notification channels: Slack, Teams, PagerDuty, webhook, email (SMTP)
- Alert deduplication + flapping suppression
- Acknowledgement + on-call rotation hooks
- SLO tracking with burn-rate alerts

---

## Phase 4 — Cost Forecasting & FinOps (v1.4)

- Time-series cost ingestion + persistence
- ARIMA / Prophet forecasting model option (alongside linear)
- Per-team budgets with anomaly detection
- "What-if" simulator (model swap, quantization, rate change)
- Showback / chargeback CSV export

---

## Phase 5 — Multi-Tenant & RBAC (v1.5)

- Tenant scoping at data + URL layer (`/t/{tenant}/api/v1/...`)
- OIDC integration (Azure AD, Okta, Keycloak)
- RBAC roles: Admin, Operator, Viewer, Billing
- Per-tenant API keys with scoped permissions
- Audit log of mutating actions

---

## Phase 6 — Agent Orchestration & Reliability (v2.0)

- LangGraph / CrewAI / AutoGen integration adapters
- Agent run timeline with span tree visualization
- Reliability scorecards (MTTR, success-rate trend, drift detector)
- Replay-from-trace developer tool

---

## Phase 7 — Edge Telemetry & Browser SDK (v2.1)

- `@vectaris/browser-sdk` to capture Web Vitals + LLM client calls
- Frontend trace stitching with backend spans
- Real-user monitoring panel

---

## Phase 8 — Distributed Tracing UI (v2.2)

- Built-in trace explorer (no Jaeger required)
- Service map auto-derived from spans
- Critical-path analysis for agent runs

---

## Phase 9 — Kubernetes / Infra Telemetry (v2.3)

- ServiceMonitor + PrometheusRule CRDs shipped
- Node / pod resource correlation with AI workloads
- GPU utilization (DCGM exporter integration)

---

## Phase 10 — Hosted Offering (v3.0)

- Managed multi-tenant SaaS deployment
- Organization billing portal
- Marketplace of provider plugins + alert templates
