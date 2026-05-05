"""Ollama LLM runtime integration.

Polls a local Ollama daemon for liveness and installed models. The runtime
is optional; when `OLLAMA_ENABLED=false` the service returns a structured
"disabled" snapshot rather than raising.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone

import httpx
import structlog

from app.config import settings
from app.models.llm import LLMModelInfo, LLMRuntimeReport, LLMRuntimeStatus

_log = structlog.get_logger("llm.ollama")


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
    if not settings.ollama_enabled:
        return _disabled_report("ollama integration disabled")

    started = time.perf_counter()
    try:
        async with httpx.AsyncClient(
            base_url=settings.ollama_base_url,
            timeout=settings.request_timeout_seconds,
        ) as client:
            response = await client.get("/api/tags")
            response.raise_for_status()
            payload = response.json()
    except httpx.HTTPError as exc:
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
