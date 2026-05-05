"""Alert evaluation service.

Combines a small in-memory rule set with live metric/agent state to produce
the active alert list. Alerts are evaluated on demand so callers always see
fresh signals without a background scheduler.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from app.models.alert import Alert, AlertSeverity
from app.services.agent_service import list_agents
from app.services.metrics_service import get_latency_summary, get_usage_summary

# Static seed alerts kept for demo / parity with prior behaviour.
_SEED_ALERTS: list[Alert] = [
    Alert(
        id="alert-seed-001",
        name="Cost budget threshold (80%)",
        severity=AlertSeverity.MEDIUM,
        message="Monthly spend has reached 80% of the configured budget.",
        triggered_at=datetime.now(tz=timezone.utc),
        source="cost-monitor",
    ),
]

# Thresholds — production deployments should source these from a config store.
P99_LATENCY_THRESHOLD_MS = 1000.0
ERROR_RATE_THRESHOLD = 0.02
AGENT_SUCCESS_RATE_FLOOR = 0.90


async def _evaluate_latency_alerts() -> list[Alert]:
    summary = await get_latency_summary()
    now = datetime.now(tz=timezone.utc)
    alerts: list[Alert] = []
    for metric in summary.models:
        if metric.p99_ms > P99_LATENCY_THRESHOLD_MS:
            alerts.append(
                Alert(
                    id=f"alert-latency-{metric.model}",
                    name=f"High P99 latency — {metric.model}",
                    severity=AlertSeverity.HIGH,
                    message=(
                        f"P99 latency {metric.p99_ms:.0f}ms exceeds "
                        f"{P99_LATENCY_THRESHOLD_MS:.0f}ms for {metric.model}"
                    ),
                    triggered_at=now,
                    source="latency-monitor",
                )
            )
    return alerts


async def _evaluate_error_rate_alerts() -> list[Alert]:
    summary = await get_usage_summary()
    now = datetime.now(tz=timezone.utc)
    if summary.error_rate <= ERROR_RATE_THRESHOLD:
        return []
    return [
        Alert(
            id="alert-error-rate",
            name="Elevated error rate",
            severity=AlertSeverity.CRITICAL,
            message=(
                f"Aggregate error rate {summary.error_rate * 100:.2f}% "
                f"exceeds {ERROR_RATE_THRESHOLD * 100:.2f}%"
            ),
            triggered_at=now,
            source="usage-monitor",
        )
    ]


def _evaluate_agent_alerts() -> list[Alert]:
    now = datetime.now(tz=timezone.utc)
    alerts: list[Alert] = []
    for agent in list_agents():
        if agent.task_success_rate < AGENT_SUCCESS_RATE_FLOOR:
            alerts.append(
                Alert(
                    id=f"alert-agent-{agent.id}",
                    name=f"Agent degraded — {agent.name}",
                    severity=AlertSeverity.MEDIUM,
                    message=(
                        f"{agent.name} success rate "
                        f"{agent.task_success_rate * 100:.1f}% is below "
                        f"{AGENT_SUCCESS_RATE_FLOOR * 100:.0f}%"
                    ),
                    triggered_at=now,
                    source="agent-monitor",
                )
            )
    return alerts


async def evaluate_alerts() -> list[Alert]:
    latency_alerts, error_alerts = await asyncio.gather(
        _evaluate_latency_alerts(),
        _evaluate_error_rate_alerts(),
    )
    return [
        *_SEED_ALERTS,
        *latency_alerts,
        *error_alerts,
        *_evaluate_agent_alerts(),
    ]
