"""Alert evaluation service.

Combines the configurable rule registry (alert_rules_service) with live
metric/agent state to produce the active alert list.  Alerts are evaluated
on demand so callers always see fresh signals without a background scheduler.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from app.models.alert import Alert
from app.services.agent_service import list_agents
from app.services.alert_rules_service import eval_rule, rules_for_metric
from app.services.metrics_service import get_latency_summary, get_usage_summary


async def _evaluate_latency_alerts() -> list[Alert]:
    summary = await get_latency_summary()
    now = datetime.now(tz=timezone.utc)
    alerts: list[Alert] = []
    p99_rules = rules_for_metric("latency_p99_ms")
    p95_rules = rules_for_metric("latency_p95_ms")
    p50_rules = rules_for_metric("latency_p50_ms")
    for metric in summary.models:
        for rule in p99_rules:
            if eval_rule(rule, metric.p99_ms):
                alerts.append(
                    Alert(
                        id=f"alert-{rule.id}-{metric.model}",
                        name=f"{rule.name} — {metric.model}",
                        severity=rule.severity,
                        message=(
                            f"P99 latency {metric.p99_ms:.0f}ms {rule.operator} "
                            f"{rule.threshold:.0f}ms for {metric.model}"
                        ),
                        triggered_at=now,
                        source=rule.source,
                    )
                )
        for rule in p95_rules:
            if eval_rule(rule, metric.p95_ms):
                alerts.append(
                    Alert(
                        id=f"alert-{rule.id}-{metric.model}",
                        name=f"{rule.name} — {metric.model}",
                        severity=rule.severity,
                        message=(
                            f"P95 latency {metric.p95_ms:.0f}ms {rule.operator} "
                            f"{rule.threshold:.0f}ms for {metric.model}"
                        ),
                        triggered_at=now,
                        source=rule.source,
                    )
                )
        for rule in p50_rules:
            if eval_rule(rule, metric.p50_ms):
                alerts.append(
                    Alert(
                        id=f"alert-{rule.id}-{metric.model}",
                        name=f"{rule.name} — {metric.model}",
                        severity=rule.severity,
                        message=(
                            f"P50 latency {metric.p50_ms:.0f}ms {rule.operator} "
                            f"{rule.threshold:.0f}ms for {metric.model}"
                        ),
                        triggered_at=now,
                        source=rule.source,
                    )
                )
    return alerts


async def _evaluate_error_rate_alerts() -> list[Alert]:
    summary = await get_usage_summary()
    now = datetime.now(tz=timezone.utc)
    alerts: list[Alert] = []
    for rule in rules_for_metric("error_rate"):
        if eval_rule(rule, summary.error_rate):
            alerts.append(
                Alert(
                    id=f"alert-{rule.id}",
                    name=rule.name,
                    severity=rule.severity,
                    message=(
                        f"Aggregate error rate {summary.error_rate * 100:.2f}% "
                        f"{rule.operator} {rule.threshold * 100:.2f}%"
                    ),
                    triggered_at=now,
                    source=rule.source,
                )
            )
    return alerts


def _evaluate_agent_alerts() -> list[Alert]:
    now = datetime.now(tz=timezone.utc)
    alerts: list[Alert] = []
    success_rules = rules_for_metric("agent_task_success_rate")
    for agent in list_agents():
        for rule in success_rules:
            if eval_rule(rule, agent.task_success_rate):
                alerts.append(
                    Alert(
                        id=f"alert-{rule.id}-{agent.id}",
                        name=f"{rule.name} — {agent.name}",
                        severity=rule.severity,
                        message=(
                            f"{agent.name} success rate "
                            f"{agent.task_success_rate * 100:.1f}% "
                            f"{rule.operator} {rule.threshold * 100:.0f}%"
                        ),
                        triggered_at=now,
                        source=rule.source,
                    )
                )
    return alerts


async def evaluate_alerts() -> list[Alert]:
    latency_alerts, error_alerts = await asyncio.gather(
        _evaluate_latency_alerts(),
        _evaluate_error_rate_alerts(),
    )
    return [
        *latency_alerts,
        *error_alerts,
        *_evaluate_agent_alerts(),
    ]
