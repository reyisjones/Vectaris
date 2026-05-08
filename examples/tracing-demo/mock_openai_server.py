"""Mock OpenAI-compatible server for distributed tracing demo.

Runs on port 9000 and responds to:
  POST /v1/chat/completions — returns a deterministic stub response

The server is instrumented with OTel so every request creates a span that
Vectaris can correlate with the parent span from the LLM proxy call.

Usage:
    python examples/tracing-demo/mock_openai_server.py

Environment:
    OTEL_ENABLED=true     — export spans via OTLP instead of console
    VECTARIS_URL          — OTLP endpoint base (default http://localhost:8000)
"""

from __future__ import annotations

import os
import time
import uuid
from typing import Any

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

VECTARIS_URL = os.getenv("VECTARIS_URL", "http://localhost:8000")
USE_OTLP = os.getenv("OTEL_ENABLED", "false").lower() == "true"

MOCK_RESPONSES = [
    "Distributed tracing allows you to follow a request as it travels through multiple "
    "services, capturing timing and metadata at each hop. For AI systems, this is "
    "invaluable because a single user query may fan out to multiple LLM calls, tool "
    "invocations, and retrieval steps — each with its own latency budget.",

    "P50 (median) is the latency that 50% of requests fall below — a typical experience. "
    "P95 covers 95% of requests and reveals outliers that affect a meaningful minority. "
    "P99 captures the worst 1% and is critical for SLAs because one slow request in a "
    "batch pipeline can block everything downstream.",

    "The W3C traceparent header (format: 00-<trace-id>-<span-id>-<flags>) is injected "
    "into outgoing HTTP requests by the OTel SDK via context propagation. The receiving "
    "service reads it, continues the same trace, and all spans share the same trace-id "
    "so they appear as a single waterfall in any trace visualiser.",
]
_response_index = 0


def init_tracing() -> None:
    resource = Resource.create({SERVICE_NAME: "mock-openai-server", "demo": "true"})
    provider = TracerProvider(resource=resource)

    if USE_OTLP:
        exporter = OTLPSpanExporter(endpoint=f"{VECTARIS_URL}/v1/traces")
        provider.add_span_processor(BatchSpanProcessor(exporter))
        print(f"[mock-openai] OTLP export → {VECTARIS_URL}/v1/traces")
    else:
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        print("[mock-openai] Console export")

    trace.set_tracer_provider(provider)


init_tracing()
app = FastAPI(title="Mock OpenAI Server", version="1.0.0")
FastAPIInstrumentor.instrument_app(app)

tracer = trace.get_tracer("mock-openai-server")


@app.post("/v1/chat/completions")
async def chat_completions(request: Request) -> Any:
    global _response_index
    body = await request.json()
    messages: list[dict] = body.get("messages", [])
    model: str = body.get("model", "mock-gpt-4o")

    with tracer.start_as_current_span(
        "mock.llm.generate",
        attributes={
            "llm.model": model,
            "llm.input_messages": len(messages),
        },
    ) as span:
        # Simulate variable latency
        fake_latency = 0.05 + (_response_index % 3) * 0.08
        time.sleep(fake_latency)

        answer = MOCK_RESPONSES[_response_index % len(MOCK_RESPONSES)]
        _response_index += 1

        prompt_tokens = sum(len(m.get("content", "").split()) for m in messages) * 2
        completion_tokens = len(answer.split()) * 2

        span.set_attributes({
            "llm.prompt_tokens": prompt_tokens,
            "llm.completion_tokens": completion_tokens,
            "llm.latency_ms": round(fake_latency * 1000),
        })

    return JSONResponse({
        "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": answer},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        },
    })


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "mock-openai-server"}


if __name__ == "__main__":
    print("[mock-openai] Starting on http://localhost:9000")
    uvicorn.run(app, host="0.0.0.0", port=9000, log_level="warning")
