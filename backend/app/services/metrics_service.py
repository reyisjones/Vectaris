"""Metrics service — queries Prometheus when configured, falls back to stubs.

Data source priority
--------------------
1. **Prometheus** — when ``PROMETHEUS_URL`` is set, latency percentiles and
   request-rate metrics are fetched via PromQL.  Metrics use the naming
   convention documented in ``app/adapters/prometheus.py``.
2. **Stub** — deterministic demo data used in development / CI when no
   Prometheus instance is available.  The ``data_source`` field in the
   response will be ``"prometheus"`` or ``"stub"`` so callers can tell which
   backend answered.
"""

from __future__ import annotations

import structlog
from datetime import datetime, timedelta, timezone

from app.adapters.prometheus import get_latency_metrics, get_usage_metrics
from app.models.metrics import LatencyMetric, LatencySummary, UsageMetric, UsageSummary

_log = structlog.get_logger("metrics_service")
_MODELS = ["gpt-4o", "gpt-4o-mini", "text-embedding-3-large"]


# ---------------------------------------------------------------------------
# Stub helpers (used when Prometheus is not configured)
# ---------------------------------------------------------------------------


def _stub_usage_summary() -> UsageSummary:
    now = datetime.now(tz=timezone.utc)
    metrics = [
        UsageMetric(
            timestamp=now - timedelta(minutes=i * 5),
            model=_MODELS[i % len(_MODELS)],
            total_requests=1200 - i * 50,
            total_tokens=450000 - i * 10000,
            error_count=i * 2,
            error_rate=round((i * 2) / max(1200 - i * 50, 1), 4),
        )
        for i in range(6)
    ]
    return UsageSummary(
        total_requests=sum(m.total_requests for m in metrics),
        total_tokens=sum(m.total_tokens for m in metrics),
        error_rate=round(sum(m.error_rate for m in metrics) / len(metrics), 4),
        models=metrics,
        data_source="stub",
    )


def _stub_latency_summary() -> LatencySummary:
    now = datetime.now(tz=timezone.utc)
    return LatencySummary(
        models=[
            LatencyMetric(timestamp=now, model="gpt-4o", p50_ms=320, p95_ms=850, p99_ms=1200),
            LatencyMetric(timestamp=now, model="gpt-4o-mini", p50_ms=180, p95_ms=420, p99_ms=680),
            LatencyMetric(
                timestamp=now,
                model="text-embedding-3-large",
                p50_ms=45,
                p95_ms=120,
                p99_ms=210,
            ),
        ],
        data_source="stub",
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def get_usage_summary() -> UsageSummary:
    """Return request counts and error rates.  Tries Prometheus first."""
    rows = await get_usage_metrics()
    if rows is None:
        _log.debug("metrics.usage.fallback_to_stub")
        return _stub_usage_summary()

    now = datetime.now(tz=timezone.utc)
    metrics = [
        UsageMetric(
            timestamp=now,
            model=r["model"],
            total_requests=r["total_requests"],
            total_tokens=r["total_tokens"],
            error_count=r["error_count"],
            error_rate=r["error_rate"],
        )
        for r in rows
    ]
    total_req = sum(m.total_requests for m in metrics)
    total_tok = sum(m.total_tokens for m in metrics)
    avg_err = round(sum(m.error_rate for m in metrics) / max(len(metrics), 1), 4)
    _log.info("metrics.usage.from_prometheus", models=len(metrics))
    return UsageSummary(
        total_requests=total_req,
        total_tokens=total_tok,
        error_rate=avg_err,
        models=metrics,
        data_source="prometheus",
    )


async def get_latency_summary() -> LatencySummary:
    """Return per-model latency percentiles.  Tries Prometheus first."""
    rows = await get_latency_metrics()
    if rows is None:
        _log.debug("metrics.latency.fallback_to_stub")
        return _stub_latency_summary()

    now = datetime.now(tz=timezone.utc)
    models = [
        LatencyMetric(
            timestamp=now,
            model=r["model"],
            p50_ms=r["p50_ms"],
            p95_ms=r["p95_ms"],
            p99_ms=r["p99_ms"],
        )
        for r in rows
    ]
    _log.info("metrics.latency.from_prometheus", models=len(models))
    return LatencySummary(models=models, data_source="prometheus")
