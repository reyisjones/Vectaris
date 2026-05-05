"""Prometheus data adapter.

Queries the Prometheus HTTP API (``/api/v1/query`` and ``/api/v1/query_range``)
to retrieve LLM latency percentiles and request usage metrics.

Configuration
-------------
``PROMETHEUS_URL`` — Base URL of the Prometheus server (e.g. ``http://prometheus:9090``).
                     Leave empty to disable; the service layer will use stub data.

Metric naming convention
------------------------
This adapter expects the following metric names to be present in Prometheus.
These are the same names used in the Grafana dashboard JSON:

* ``vectaris_llm_request_duration_seconds`` (histogram)
* ``vectaris_llm_requests_total`` (counter, labels: ``model``, ``status``)

Adjust ``_METRIC_*`` constants below if your scrape jobs use different names.
"""

from __future__ import annotations

import structlog

from app.config import settings

_log = structlog.get_logger("adapter.prometheus")

_METRIC_LATENCY_HIST = "vectaris_llm_request_duration_seconds"
_METRIC_REQUESTS_TOTAL = "vectaris_llm_requests_total"


def _is_configured() -> bool:
    return bool(settings.prometheus_url)


async def query_instant(promql: str) -> list[dict] | None:
    """Execute an instant PromQL query.  Returns the ``result`` list or ``None`` on error."""
    if not _is_configured():
        return None

    import httpx

    url = settings.prometheus_url.rstrip("/") + "/api/v1/query"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params={"query": promql})
            resp.raise_for_status()
            data = resp.json()
        if data.get("status") != "success":
            _log.warning("prometheus.query_failed", promql=promql, response=data)
            return None
        return data["data"]["result"]
    except Exception as exc:  # noqa: BLE001
        _log.warning("prometheus.unreachable", error=str(exc))
        return None


async def get_latency_metrics() -> list[dict] | None:
    """Return per-model latency percentiles from Prometheus.

    Returns a list of dicts with keys: ``model``, ``p50_ms``, ``p95_ms``, ``p99_ms``.
    Returns ``None`` when Prometheus is unavailable or not configured.
    """
    if not _is_configured():
        return None

    # Query all three percentiles in parallel
    import asyncio

    window = "5m"
    p50_q = f"histogram_quantile(0.50, sum(rate({_METRIC_LATENCY_HIST}_bucket[{window}])) by (le, model))"
    p95_q = f"histogram_quantile(0.95, sum(rate({_METRIC_LATENCY_HIST}_bucket[{window}])) by (le, model))"
    p99_q = f"histogram_quantile(0.99, sum(rate({_METRIC_LATENCY_HIST}_bucket[{window}])) by (le, model))"

    p50_res, p95_res, p99_res = await asyncio.gather(
        query_instant(p50_q),
        query_instant(p95_q),
        query_instant(p99_q),
    )

    if p50_res is None or p95_res is None or p99_res is None:
        return None

    def _index(result: list[dict]) -> dict[str, float]:
        """Map model label → value in milliseconds."""
        return {
            r["metric"].get("model", "unknown"): round(float(r["value"][1]) * 1000, 2)
            for r in result
            if r.get("metric") and r.get("value")
        }

    p50 = _index(p50_res)
    p95 = _index(p95_res)
    p99 = _index(p99_res)
    models = sorted(set(p50) | set(p95) | set(p99))

    return [
        {
            "model": m,
            "p50_ms": p50.get(m, 0.0),
            "p95_ms": p95.get(m, 0.0),
            "p99_ms": p99.get(m, 0.0),
        }
        for m in models
    ]


async def get_usage_metrics() -> list[dict] | None:
    """Return per-model request counts and error rates from Prometheus.

    Returns a list of dicts with keys: ``model``, ``total_requests``,
    ``total_tokens``, ``error_count``, ``error_rate``.
    Returns ``None`` when Prometheus is unavailable or not configured.

    Note: ``total_tokens`` is not tracked by the default Vectaris Prometheus
    metrics and will be 0 unless you add a ``vectaris_llm_tokens_total`` counter.
    """
    if not _is_configured():
        return None

    window = "5m"
    total_q = f"sum(rate({_METRIC_REQUESTS_TOTAL}[{window}])) by (model)"
    error_q = f'sum(rate({_METRIC_REQUESTS_TOTAL}{{status="error"}}[{window}])) by (model)'

    import asyncio

    total_res, error_res = await asyncio.gather(
        query_instant(total_q),
        query_instant(error_q),
    )

    if total_res is None or error_res is None:
        return None

    def _index(result: list[dict]) -> dict[str, float]:
        return {
            r["metric"].get("model", "unknown"): float(r["value"][1])
            for r in result
            if r.get("metric") and r.get("value")
        }

    totals = _index(total_res)
    errors = _index(error_res)
    models = sorted(totals)

    return [
        {
            "model": m,
            "total_requests": int(totals.get(m, 0)),
            "total_tokens": 0,  # extend with vectaris_llm_tokens_total if available
            "error_count": int(errors.get(m, 0)),
            "error_rate": round(errors.get(m, 0) / max(totals.get(m, 1), 1e-9), 4),
        }
        for m in models
    ]
