# Tutorial: Instrumenting a Custom AI Agent for Vectaris

This guide shows how to add observability to **any Python AI agent** and stream
its telemetry into Vectaris so it appears in the dashboard.

You will learn to:
1. Register the agent with Vectaris
2. Emit OpenTelemetry traces from LLM calls
3. Report heartbeats so Vectaris can track health
4. Forward structured logs and custom metrics

---

## Prerequisites

| Requirement | Notes |
|-------------|-------|
| Vectaris running locally | `docker compose up` or `uvicorn app.main:app` |
| Python 3.9+ | The example uses asyncio |
| `pip install opentelemetry-sdk opentelemetry-exporter-otlp-proto-http httpx` | Telemetry + HTTP client |

Set the Vectaris base URL once:

```bash
export VECTARIS_URL=http://localhost:8000
export VECTARIS_API_KEY=          # leave blank if running in open mode
```

---

## Step 1 — Register the Agent

Before an agent appears in the dashboard it must register itself.
Call `POST /api/v1/agents` with a JSON body:

```python
import httpx, os

VECTARIS_URL = os.getenv("VECTARIS_URL", "http://localhost:8000")
API_KEY = os.getenv("VECTARIS_API_KEY", "")

def _headers() -> dict:
    h = {"Content-Type": "application/json"}
    if API_KEY:
        h["X-API-Key"] = API_KEY
    return h

def register_agent(name: str, model: str, provider: str = "openai") -> str:
    """Register the agent and return its assigned ID."""
    resp = httpx.post(
        f"{VECTARIS_URL}/api/v1/agents",
        json={"name": name, "model": model, "provider": provider},
        headers=_headers(),
        timeout=10,
    )
    resp.raise_for_status()
    agent_id: str = resp.json()["id"]
    print(f"Registered agent {name!r} with ID {agent_id}")
    return agent_id
```

---

## Step 2 — Initialise OpenTelemetry

Vectaris ingests OTLP traces. Initialise the OTel SDK once at startup:

```python
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

def init_telemetry(service_name: str, agent_id: str) -> trace.Tracer:
    resource = Resource.create({
        SERVICE_NAME: service_name,
        "agent.id": agent_id,
    })
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(
        endpoint=f"{VECTARIS_URL}/v1/traces",
        headers=_headers(),
    )
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    return trace.get_tracer(service_name)
```

---

## Step 3 — Instrument LLM Calls

Wrap every LLM call in a span so Vectaris captures latency and token usage:

```python
import time
from opentelemetry import trace
from opentelemetry.trace import StatusCode

tracer: trace.Tracer  # set after init_telemetry()

async def call_llm(
    client: httpx.AsyncClient,
    model: str,
    messages: list[dict],
) -> dict:
    with tracer.start_as_current_span(
        "llm.chat",
        attributes={
            "llm.model": model,
            "llm.message_count": len(messages),
        },
    ) as span:
        start = time.monotonic()
        try:
            resp = await client.post(
                f"{VECTARIS_URL}/api/v1/llm/chat",
                json={"model": model, "messages": messages},
                headers=_headers(),
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()

            latency_ms = (time.monotonic() - start) * 1000
            usage = data.get("usage", {})

            span.set_attributes({
                "llm.latency_ms": round(latency_ms),
                "llm.prompt_tokens": usage.get("prompt_tokens", 0),
                "llm.completion_tokens": usage.get("completion_tokens", 0),
                "llm.total_tokens": usage.get("total_tokens", 0),
            })
            span.set_status(StatusCode.OK)
            return data
        except Exception as exc:
            span.record_exception(exc)
            span.set_status(StatusCode.ERROR, str(exc))
            raise
```

> **Tip:** If you use the Vectaris LLM proxy (`/api/v1/llm/chat`) the proxy itself
> creates a server-side span and correlates it to your client span automatically
> via the `traceparent` header that OTel injects into outgoing requests.

---

## Step 4 — Send Heartbeats

Vectaris tracks agent health by expecting regular `PATCH /api/v1/agents/{id}/heartbeat`
calls. An agent that misses more than 3 consecutive heartbeat windows is marked
**degraded** or **unhealthy**.

```python
import asyncio

HEARTBEAT_INTERVAL = 30  # seconds

async def heartbeat_loop(agent_id: str, success_rate: float, tasks_per_min: float):
    """Continuously send heartbeats in the background."""
    async with httpx.AsyncClient() as client:
        while True:
            try:
                await client.patch(
                    f"{VECTARIS_URL}/api/v1/agents/{agent_id}/heartbeat",
                    json={
                        "task_success_rate": success_rate,
                        "tasks_per_minute": tasks_per_min,
                    },
                    headers=_headers(),
                    timeout=5,
                )
            except Exception as exc:
                print(f"Heartbeat failed: {exc}")
            await asyncio.sleep(HEARTBEAT_INTERVAL)
```

Start the loop as a background task early in your agent's lifecycle:

```python
asyncio.create_task(heartbeat_loop(agent_id, success_rate=0.98, tasks_per_min=4.0))
```

---

## Step 5 — Complete Example

Putting it all together — a minimal agent that answers user questions and reports
its telemetry to Vectaris:

```python
"""minimal_agent.py — complete instrumented agent example."""
import asyncio
import os
import time

import httpx
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import StatusCode

VECTARIS_URL = os.getenv("VECTARIS_URL", "http://localhost:8000")
API_KEY = os.getenv("VECTARIS_API_KEY", "")

tracer: trace.Tracer


def _headers() -> dict:
    h = {"Content-Type": "application/json"}
    if API_KEY:
        h["X-API-Key"] = API_KEY
    return h


def register_agent(name: str, model: str) -> str:
    resp = httpx.post(
        f"{VECTARIS_URL}/api/v1/agents",
        json={"name": name, "model": model},
        headers=_headers(),
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["id"]


def init_telemetry(service_name: str, agent_id: str) -> None:
    global tracer
    resource = Resource.create({SERVICE_NAME: service_name, "agent.id": agent_id})
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(
        endpoint=f"{VECTARIS_URL}/v1/traces", headers=_headers()
    )
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    tracer = trace.get_tracer(service_name)


async def ask(client: httpx.AsyncClient, question: str) -> str:
    with tracer.start_as_current_span("agent.ask", attributes={"question": question}) as span:
        start = time.monotonic()
        try:
            data = (
                await client.post(
                    f"{VECTARIS_URL}/api/v1/llm/chat",
                    json={
                        "model": "gpt-4o",
                        "messages": [
                            {"role": "system", "content": "You are a helpful assistant."},
                            {"role": "user", "content": question},
                        ],
                    },
                    headers=_headers(),
                    timeout=60,
                )
            ).json()
            span.set_attributes({
                "llm.latency_ms": round((time.monotonic() - start) * 1000),
                "llm.total_tokens": data.get("usage", {}).get("total_tokens", 0),
            })
            span.set_status(StatusCode.OK)
            return data["choices"][0]["message"]["content"]
        except Exception as exc:
            span.record_exception(exc)
            span.set_status(StatusCode.ERROR, str(exc))
            return f"Error: {exc}"


async def heartbeat_loop(agent_id: str) -> None:
    async with httpx.AsyncClient() as client:
        while True:
            try:
                await client.patch(
                    f"{VECTARIS_URL}/api/v1/agents/{agent_id}/heartbeat",
                    json={"task_success_rate": 0.99, "tasks_per_minute": 2.0},
                    headers=_headers(),
                    timeout=5,
                )
            except Exception:
                pass
            await asyncio.sleep(30)


async def main() -> None:
    agent_id = register_agent(name="demo-agent", model="gpt-4o")
    init_telemetry("demo-agent", agent_id)
    asyncio.create_task(heartbeat_loop(agent_id))

    async with httpx.AsyncClient() as client:
        questions = [
            "What are the OWASP Top 10 for LLMs?",
            "How does Prometheus scrape metrics?",
            "Explain p99 latency in one sentence.",
        ]
        for q in questions:
            answer = await ask(client, q)
            print(f"Q: {q}\nA: {answer[:120]}…\n")
            await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(main())
```

Run it:
```bash
python minimal_agent.py
```

Then open the Vectaris dashboard at http://localhost:3000 — you should see
`demo-agent` appear in the Agent Health table with live latency metrics streaming
from the LLM calls.

---

## Step 6 — Verify in the Dashboard

1. **Agent Health table** → `demo-agent` with status **healthy**
2. **Latency chart** → bars for `gpt-4o` reflecting the real call latencies
3. **Costs page** → token usage accumulating under the `gpt-4o` model

If the agent does not appear, check:
- Vectaris backend is running: `curl http://localhost:8000/health`
- Registration succeeded: `curl http://localhost:8000/api/v1/agents`
- OTel endpoint is reachable (the backend logs OTLP export errors at `WARNING` level)

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| 401 Unauthorized | API_KEY env var not set | Export `VECTARIS_API_KEY` |
| 429 Too Many Requests | LLM proxy rate limit hit | Reduce request frequency or increase limit |
| Agent status `unknown` | Heartbeat not reaching backend | Check network; confirm `/heartbeat` endpoint responding |
| No spans in traces | OTLP exporter not configured | Verify `init_telemetry()` is called before `ask()` |
| Latency chart shows stubs | Prometheus not configured | Expected in dev; set `PROMETHEUS_URL` for real data |

---

## Next Steps

- **Multi-agent systems**: Register each sub-agent separately and use OTel baggage
  to propagate the `agent.id` across service boundaries.
- **Custom metrics**: Export Prometheus metrics from your agent and add a
  `ServiceMonitor` that points to your agent's `/metrics` endpoint.
- **Alert rules**: Use `POST /api/v1/alerts/rules` to create rules that trigger
  webhooks when your agent's error rate exceeds a threshold.
- **Cost attribution**: Pass a `tenant_id` claim in the OIDC JWT to track
  per-tenant costs in the Costs page.
