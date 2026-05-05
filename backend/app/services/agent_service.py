from __future__ import annotations

from datetime import datetime, timezone

from app.models.agent import Agent, AgentHealth, AgentStatus

_AGENTS: list[Agent] = [
    Agent(
        id="agent-001",
        name="research-agent",
        model="gpt-4o",
        status=AgentStatus.HEALTHY,
        uptime_seconds=86400,
        task_success_rate=0.98,
        tasks_per_minute=4.2,
        last_seen=datetime.now(tz=timezone.utc),
    ),
    Agent(
        id="agent-002",
        name="summarizer-agent",
        model="gpt-4o-mini",
        status=AgentStatus.DEGRADED,
        uptime_seconds=3600,
        task_success_rate=0.87,
        tasks_per_minute=12.5,
        last_seen=datetime.now(tz=timezone.utc),
    ),
    Agent(
        id="agent-003",
        name="embedding-indexer",
        model="text-embedding-3-large",
        status=AgentStatus.HEALTHY,
        uptime_seconds=172800,
        task_success_rate=0.999,
        tasks_per_minute=60.0,
        last_seen=datetime.now(tz=timezone.utc),
    ),
]


def list_agents() -> list[Agent]:
    return _AGENTS


def get_agent_health(agent_id: str) -> AgentHealth | None:
    agent = next((a for a in _AGENTS if a.id == agent_id), None)
    if not agent:
        return None
    return AgentHealth(
        agent_id=agent.id,
        status=agent.status,
        latency_ms=85.0 if agent.status == AgentStatus.HEALTHY else 950.0,
        error_rate=1.0 - agent.task_success_rate,
        checked_at=datetime.now(tz=timezone.utc),
    )
