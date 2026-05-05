# Vectaris — AI Platform Dashboard

> Production-grade observability dashboard for AI systems — monitor usage, latency, cost, errors, agent health, and local LLM runtimes in real time.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue)](https://python.org)
[![React 18](https://img.shields.io/badge/React-18-61DAFB)](https://react.dev)
[![OpenTelemetry](https://img.shields.io/badge/OpenTelemetry-native-orange)](https://opentelemetry.io)

---

## Overview

Vectaris provides a unified observability layer for AI workloads. It aggregates telemetry from LLM inference endpoints, agent runtimes, and cloud cost APIs to give platform engineers a single pane of glass.

### Capabilities

- **Usage metrics** — token, request, and error-rate roll-ups per model
- **Latency metrics** — P50 / P95 / P99 per model and endpoint
- **Cost attribution** — by model and by team, with linear forecast
- **Agent health** — uptime, success rate, throughput, status badges
- **Alerts** — rules evaluated live against current telemetry
- **LLM runtime monitoring** — Ollama liveness + installed model registry
- **OpenTelemetry-native** — OTLP traces and metrics, Prometheus scrape endpoint
- **Structured JSON logs** with trace correlation IDs

---

## Tech Stack

| Layer            | Technology                                      |
|------------------|-------------------------------------------------|
| Frontend         | React 18 · Vite · TypeScript · React Router · Recharts · TanStack Query |
| Backend          | Python 3.12 · FastAPI · Pydantic v2 · structlog |
| Telemetry        | OpenTelemetry SDK · OTLP exporter · Prometheus  |
| Containerization | Docker · Docker Compose                         |
| Orchestration    | Kubernetes (AKS-ready)                          |
| Cloud            | Azure Container Apps / AKS                      |
| CI/CD            | GitHub Actions                                  |

---

## Quick Start

### Prerequisites

- Docker 24+ and Docker Compose v2
- Node.js 20+ (for local frontend development)
- Python 3.12+ (for local backend development)

### Run with Docker Compose

```bash
git clone https://github.com/your-org/Vectaris.git
cd Vectaris
cp backend/.env.example backend/.env
docker compose up --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Prometheus metrics | http://localhost:8000/metrics |

### Run Locally (Development)

**Backend:**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Liveness probe |
| GET | `/ready`  | Readiness probe |
| GET | `/metrics` | Prometheus-format metrics |
| GET | `/api/v1/metrics/usage`   | Token / request / error roll-ups |
| GET | `/api/v1/metrics/latency` | P50 / P95 / P99 per model |
| GET | `/api/v1/agents`             | Registered agents with status |
| GET | `/api/v1/agents/{id}/health` | Per-agent health snapshot |
| GET | `/api/v1/costs`              | Cost breakdown by model and team |
| GET | `/api/v1/costs/forecast`     | Linear cost projection |
| GET | `/api/v1/alerts`             | Active alerts (live evaluation) |
| GET | `/api/v1/llm/runtime`        | Ollama runtime status & installed models |

Full Swagger docs: `http://localhost:8000/docs`.

---

## Configuration

All backend settings are environment-driven. See [backend/.env.example](backend/.env.example).

| Variable | Default | Purpose |
|----------|---------|---------|
| `ENVIRONMENT` | `development` | Tag emitted in logs/traces |
| `LOG_LEVEL` | `INFO` | structlog filter level |
| `CORS_ORIGINS` | `["http://localhost:3000","http://localhost:5173"]` | Allowed browser origins |
| `OTEL_ENABLED` | `false` | Toggle OTLP exporters |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://localhost:4317` | OTLP gRPC collector |
| `OLLAMA_ENABLED` | `false` | Enable local LLM runtime checks |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama daemon URL |
| `AZURE_MONITOR_CONNECTION_STRING` | _(empty)_ | Optional Azure Monitor |

---

## Deployment

### Kubernetes

```bash
kubectl apply -f deploy/kubernetes/namespace.yaml
kubectl apply -f deploy/kubernetes/
```

The backend manifest enables non-root, read-only filesystem, liveness/readiness probes, resource limits, and an HPA (2–10 replicas at 70 % CPU).

See [ARCHITECTURE.md](ARCHITECTURE.md) for diagrams and [ROADMAP.md](ROADMAP.md) for the feature plan.

---

## Observability

Vectaris is itself instrumented end-to-end:

- **Traces** via OpenTelemetry SDK → OTLP → Azure Monitor / Jaeger / Tempo
- **Metrics** via Prometheus client (`/metrics`) and OTLP MeterProvider
- **Logs** as structured JSON to stdout, with `trace_id` / `request_id` injected by middleware

Every HTTP request is tagged with an `X-Request-ID` header (auto-generated if not provided), counted in `http_requests_total`, and timed via the `http_request_duration_seconds` histogram.

---

## Project Structure

```
Vectaris/
├── frontend/                       # React 18 + Vite + TS + React Router
│   ├── src/
│   │   ├── components/             # MetricCard, LatencyChart, AlertsList…
│   │   ├── pages/                  # Dashboard / Agents / Costs / Alerts / LLM
│   │   ├── services/api.ts         # Typed Axios client
│   │   └── styles/global.css       # Theme
│   ├── nginx.conf                  # SPA routing
│   ├── tsconfig*.json              # TypeScript configs
│   └── Dockerfile
├── backend/                        # FastAPI + Pydantic v2
│   ├── app/
│   │   ├── main.py                 # App factory + middleware + lifespan
│   │   ├── config.py               # pydantic-settings
│   │   ├── logging_config.py       # structlog JSON renderer
│   │   ├── middleware.py           # Request-ID + Prometheus metrics
│   │   ├── routers/                # metrics, agents, costs, alerts, llm, health
│   │   ├── models/                 # Pydantic schemas
│   │   ├── services/               # Business logic (incl. Ollama, alerts)
│   │   └── telemetry/setup.py      # OTel tracer + meter providers
│   ├── tests/                      # pytest API tests
│   └── Dockerfile
├── deploy/
│   └── kubernetes/                 # Namespace, Deployment, Service, HPA
├── .github/workflows/ci.yml
├── docker-compose.yml
├── ARCHITECTURE.md
├── ROADMAP.md
├── TODO.md
└── CLEANUP_REPORT.md
```

---

## Contributing

1. Fork & branch: `git checkout -b feat/your-feature`
2. Backend tests: `cd backend && pytest`
3. Frontend lint/build: `cd frontend && npm run lint && npm run build`
4. Open a PR — CI must pass.

---

## License

MIT — see [LICENSE](LICENSE).
