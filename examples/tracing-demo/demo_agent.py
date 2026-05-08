"""Distributed Tracing Demo

Demonstrates end-to-end OpenTelemetry tracing across:
  1. Demo agent (this script)          — root span
  2. Vectaris LLM proxy backend        — child span (via traceparent propagation)
  3. Mock OpenAI server (local)        — leaf span (instrumented with OTel)

Architecture:
    demo_agent.py
        └── POST /api/v1/llm/chat   (Vectaris backend — auto-instrumented)
                └── POST /v1/chat/completions  (mock_openai_server.py)

Run order:
    # Terminal 1 — mock OpenAI server
    python examples/tracing-demo/mock_openai_server.py

    # Terminal 2 — Vectaris backend (pointing at mock)
    OPENAI_BASE_URL=http://localhost:9000 uvicorn app.main:app --port 8000

    # Terminal 3 — demo agent
    python examples/tracing-demo/demo_agent.py

Traces are exported to the Vectaris OTLP endpoint (http://localhost:8000/v1/traces)
if it is configured, or printed to stdout via the ConsoleSpanExporter as a fallback.
"""

from __future__ import annotations

import asyncio
import os
import time
from typing import Any

import httpx
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.trace import StatusCode
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

VECTARIS_URL = os.getenv("VECTARIS_URL", "http://localhost:8000")
API_KEY = os.getenv("VECTARIS_API_KEY", "")
USE_OTLP = os.getenv("OTEL_ENABLED", "false").lower() == "true"

propagator = TraceContextTextMapPropagator()
_tracer: trace.Tracer


def _headers() -> dict[str, str]:
    h: dict[str, str] = {"Content-Type": "application/json"}
    if API_KEY:
        h["X-API-Key"] = API_KEY
    return h


# ---------------------------------------------------------------------------
# OTel setup
# ---------------------------------------------------------------------------

def init_tracing(service_name: str) -> None:
    global _tracer
    resource = Resource.create({SERVICE_NAME: service_name, "demo": "true"})
    provider = TracerProvider(resource=resource)

    if USE_OTLP:
        exporter = OTLPSpanExporter(
            endpoint=f"{VECTARIS_URL}/v1/traces",
            headers=_headers(),
        )
        provider.add_span_processor(BatchSpanProcessor(exporter))
        print(f"[tracing-demo] OTLP export → {VECTARIS_URL}/v1/traces")
    else:
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        print("[tracing-demo] Console export (set OTEL_ENABLED=true for OTLP)")

    trace.set_tracer_provider(provider)
    _tracer = trace.get_tracer(service_name, schema_url="https://opentelemetry.io/schemas/1.11.0")


# ---------------------------------------------------------------------------
# Agent logic
# ---------------------------------------------------------------------------

async def register_agent(client: httpx.AsyncClient) -> str:
    resp = await client.post(
        f"{VECTARIS_URL}/api/v1/agents",
        json={"name": "tracing-demo-agent", "model": "mock-gpt-4o", "provider": "mock"},
        headers=_headers(),
        timeout=10,
    )
    resp.raise_for_status()
    agent_id: str = resp.json()["id"]
    print(f"[tracing-demo] Registered agent {agent_id}")
    return agent_id


async def call_llm_via_proxy(
    client: httpx.AsyncClient,
    question: str,
    parent_span: Any,
) -> dict:
    """Call the Vectaris LLM proxy with W3C traceparent propagation."""
    headers = dict(_headers())

    # Inject the current trace context so the backend can link its span
    ctx = trace.set_span_in_context(parent_span)
    propagator.inject(headers, context=ctx)

    with _tracer.start_as_current_span(
        "llm.proxy.call",
        context=ctx,
        attributes={"llm.question": question[:100]},
    ) as span:
        start = time.monotonic()
        try:
            resp = await client.post(
                f"{VECTARIS_URL}/api/v1/llm/chat",
                json={
                    "model": "mock-gpt-4o",
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": question},
                    ],
                },
                headers=headers,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            elapsed_ms = round((time.monotonic() - start) * 1000)
            span.set_attributes({
                "llm.latency_ms": elapsed_ms,
                "llm.total_tokens": data.get("usage", {}).get("total_tokens", 0),
                "llm.model": data.get("model", "unknown"),
            })
            span.set_status(StatusCode.OK)
            return data
        except Exception as exc:
            span.record_exception(exc)
            span.set_status(StatusCode.ERROR, str(exc))
            raise


async def run_demo(agent_id: str) -> None:
    questions = [
        "What is distributed tracing and why does it matter for AI systems?",
        "Explain the difference between p50, p95, and p99 latency.",
        "How does the W3C traceparent header enable trace propagation?",
    ]

    async with httpx.AsyncClient() as client:
        for i, question in enumerate(questions, 1):
            print(f"\n[tracing-demo] Question {i}/{len(questions)}")
            print(f"  Q: {question}")

            with _tracer.start_as_current_span(
                "demo.question",
                attributes={
                    "agent.id": agent_id,
                    "question.index": i,
                    "question.text": question[:100],
                },
            ) as root_span:
                try:
                    data = await call_llm_via_proxy(client, question, root_span)
                    answer = data["choices"][0]["message"]["content"]
                    print(f"  A: {answer[:200]}…")
                    root_span.set_status(StatusCode.OK)
                except Exception as exc:
                    print(f"  Error: {exc}")
                    root_span.set_status(StatusCode.ERROR, str(exc))

            await asyncio.sleep(1)

    print("\n[tracing-demo] Done. Trace IDs printed above (Console) or sent to OTLP.")


async def main() -> None:
    init_tracing("tracing-demo-agent")

    async with httpx.AsyncClient() as client:
        agent_id = await register_agent(client)

    await run_demo(agent_id)


if __name__ == "__main__":
    asyncio.run(main())
