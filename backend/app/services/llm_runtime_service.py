"""Ollama LLM runtime integration.

Polls a local Ollama daemon for liveness and installed models. The runtime
is optional; when ``OLLAMA_ENABLED=false`` the service returns a structured
"disabled" snapshot rather than raising.

OTel context propagation
------------------------
* ``HTTPXClientInstrumentor`` (attached in ``telemetry/setup.py``) patches the
  default httpx transport globally so trace/baggage headers are injected
  automatically on every outbound request.
* We additionally inject the current trace context manually via
  ``opentelemetry.propagate.inject`` so context is propagated even when the
  global instrumentor is not active (e.g. unit-test mode).
* Each probe is wrapped in a manual ``llm.runtime.probe`` span to make the
  full round-trip observable as a single, labelled unit.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone

import httpx
import structlog
from opentelemetry import propagate, trace

from app.config import settings
from app.models.llm import LLMModelInfo, LLMRuntimeReport, LLMRuntimeStatus

_log = structlog.get_logger("llm.ollama")
_tracer = trace.get_tracer("vectaris.llm.runtime")


def _disabled_report(reason: str) -> LLMRuntimeReport:
    return LLMRuntimeReport(
        status=LLMRuntimeStatus(
            provider="ollama",
            base_url=settings.ollama_base_url,
            reachable=False,
            error=reason,
            checked_at=datetime.now(tz=timezone.utc),
        ),
        models=[],
    )


async def get_runtime_report() -> LLMRuntimeReport:
    """Probe the Ollama daemon and return a structured runtime report."""
    if not settings.ollama_enabled:
        return _disabled_report("Ollama integration is disabled (OLLAMA_ENABLED=false)")

    started = time.perf_counter()

    with _tracer.start_as_current_span(
        "llm.runtime.probe",
        attributes={
            "llm.provider": "ollama",
            "llm.base_url": settings.ollama_base_url,
        },
    ) as span:
        # Build headers with current trace context so the downstream Ollama
        # service (if it were instrumented) would receive the span context.
        headers: dict[str, str] = {}
        propagate.inject(headers)

        try:
            async with httpx.AsyncClient(
                base_url=settings.ollama_base_url,
                timeout=settings.request_timeout_seconds,
                headers=headers,
            ) as client:
                response = await client.get("/api/tags")
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPError as exc:
            span.set_attribute("llm.reachable", False)
            span.record_exception(exc)
            _log.warning("ollama.unreachable", error=str(exc))
            return LLMRuntimeReport(
                status=LLMRuntimeStatus(
                    provider="ollama",
                    base_url=settings.ollama_base_url,
                    reachable=False,
                    error=str(exc),
                    checked_at=datetime.now(tz=timezone.utc),
                ),
                models=[],
            )

        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        models = [_parse_model(m) for m in payload.get("models", [])]
        span.set_attribute("llm.reachable", True)
        span.set_attribute("llm.latency_ms", latency_ms)
        span.set_attribute("llm.models_count", len(models))
        _log.info("ollama.probed", latency_ms=latency_ms, models=len(models))
        return LLMRuntimeReport(
            status=LLMRuntimeStatus(
                provider="ollama",
                base_url=settings.ollama_base_url,
                reachable=True,
                latency_ms=latency_ms,
                checked_at=datetime.now(tz=timezone.utc),
            ),
            models=models,
        )


def _parse_model(raw: dict) -> LLMModelInfo:
    details = raw.get("details") or {}
    modified = raw.get("modified_at")
    parsed_modified: datetime | None = None
    if isinstance(modified, str):
        try:
            parsed_modified = datetime.fromisoformat(modified.replace("Z", "+00:00"))
        except ValueError:
            parsed_modified = None
    return LLMModelInfo(
        name=raw.get("name", "unknown"),
        size_bytes=int(raw.get("size", 0) or 0),
        parameter_size=details.get("parameter_size"),
        quantization=details.get("quantization_level"),
        modified_at=parsed_modified,
    )
