from datetime import datetime, timedelta, timezone

from app.models.metrics import LatencyMetric, LatencySummary, UsageMetric, UsageSummary

# Stub data — replace with real telemetry queries (Azure Monitor, PromQL, etc.)
_MODELS = ["gpt-4o", "gpt-4o-mini", "text-embedding-3-large"]


def get_usage_summary() -> UsageSummary:
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
    )


def get_latency_summary() -> LatencySummary:
    now = datetime.now(tz=timezone.utc)
    return LatencySummary(
        models=[
            LatencyMetric(timestamp=now, model="gpt-4o", p50_ms=320, p95_ms=850, p99_ms=1200),
            LatencyMetric(timestamp=now, model="gpt-4o-mini", p50_ms=180, p95_ms=420, p99_ms=680),
            LatencyMetric(
                timestamp=now, model="text-embedding-3-large", p50_ms=45, p95_ms=120, p99_ms=210
            ),
        ]
    )
