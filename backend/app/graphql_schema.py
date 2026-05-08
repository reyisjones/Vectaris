"""GraphQL schema and resolver definitions.

Exposes a read-only GraphQL endpoint at ``/graphql`` alongside the REST API.
Uses Strawberry with the FastAPI integration.

Supported queries:
    usageMetrics  — aggregate token/request counts
    latencyMetrics — per-model p50/p95/p99
    agents         — registered agent list
    agent(id)      — single agent lookup
    alerts         — active alert list
"""

from __future__ import annotations

from typing import Optional

import strawberry
from strawberry.fastapi import GraphQLRouter

from app.services.agent_service import list_agents as _list_agents
from app.services.agent_service import get_agent as _get_agent
from app.services.metrics_service import get_usage_summary, get_latency_summary
from app.services.alert_service import evaluate_alerts as _evaluate_alerts


# ---------------------------------------------------------------------------
# GraphQL types
# ---------------------------------------------------------------------------


@strawberry.type
class UsageMetricGQL:
    timestamp: str
    model: str
    total_requests: int
    total_tokens: int
    error_count: int
    error_rate: float


@strawberry.type
class UsageSummaryGQL:
    total_requests: int
    total_tokens: int
    error_rate: float
    models: list[UsageMetricGQL]
    data_source: str


@strawberry.type
class LatencyMetricGQL:
    timestamp: str
    model: str
    p50_ms: float
    p95_ms: float
    p99_ms: float


@strawberry.type
class LatencySummaryGQL:
    models: list[LatencyMetricGQL]
    data_source: str


@strawberry.type
class AgentGQL:
    id: str
    name: str
    model: str
    status: str
    uptime_seconds: float
    task_success_rate: float
    tasks_per_minute: float
    last_seen: str


@strawberry.type
class AlertGQL:
    id: str
    name: str
    severity: str
    message: str
    triggered_at: str
    resolved: bool
    source: Optional[str]


# ---------------------------------------------------------------------------
# Query resolvers
# ---------------------------------------------------------------------------


@strawberry.type
class Query:
    @strawberry.field(description="Aggregate token and request counts across all models.")
    async def usage_metrics(self) -> UsageSummaryGQL:
        data = await get_usage_summary()
        return UsageSummaryGQL(
            total_requests=data.total_requests,
            total_tokens=data.total_tokens,
            error_rate=data.error_rate,
            data_source=data.data_source,
            models=[
                UsageMetricGQL(
                    timestamp=m.timestamp.isoformat(),
                    model=m.model,
                    total_requests=m.total_requests,
                    total_tokens=m.total_tokens,
                    error_count=m.error_count,
                    error_rate=m.error_rate,
                )
                for m in data.models
            ],
        )

    @strawberry.field(description="P50/P95/P99 latency per model.")
    async def latency_metrics(self) -> LatencySummaryGQL:
        data = await get_latency_summary()
        return LatencySummaryGQL(
            data_source=data.data_source,
            models=[
                LatencyMetricGQL(
                    timestamp=m.timestamp.isoformat(),
                    model=m.model,
                    p50_ms=m.p50_ms,
                    p95_ms=m.p95_ms,
                    p99_ms=m.p99_ms,
                )
                for m in data.models
            ],
        )

    @strawberry.field(description="List all registered agents.")
    def agents(self) -> list[AgentGQL]:
        items = _list_agents()
        return [
            AgentGQL(
                id=a.id,
                name=a.name,
                model=a.model,
                status=a.status,
                uptime_seconds=a.uptime_seconds,
                task_success_rate=a.task_success_rate,
                tasks_per_minute=a.tasks_per_minute,
                last_seen=a.last_seen.isoformat(),
            )
            for a in items
        ]

    @strawberry.field(description="Look up a single agent by ID.")
    def agent(self, id: str) -> Optional[AgentGQL]:
        a = _get_agent(id)
        if a is None:
            return None
        return AgentGQL(
            id=a.id,
            name=a.name,
            model=a.model,
            status=a.status,
            uptime_seconds=a.uptime_seconds,
            task_success_rate=a.task_success_rate,
            tasks_per_minute=a.tasks_per_minute,
            last_seen=a.last_seen.isoformat(),
        )

    @strawberry.field(description="Return active (non-resolved) alerts.")
    async def alerts(self) -> list[AlertGQL]:
        items = await _evaluate_alerts()
        return [
            AlertGQL(
                id=a.id,
                name=a.name,
                severity=a.severity,
                message=a.message,
                triggered_at=a.triggered_at.isoformat(),
                resolved=a.resolved,
                source=a.source,
            )
            for a in items
        ]


# ---------------------------------------------------------------------------
# Router — mount at /graphql in main.py
# ---------------------------------------------------------------------------

schema = strawberry.Schema(query=Query)

graphql_router: GraphQLRouter = GraphQLRouter(
    schema,
    graphql_ide="graphiql",  # interactive IDE at GET /graphql
)
