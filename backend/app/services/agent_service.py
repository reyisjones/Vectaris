"""Agent registry — in-memory store with full CRUD.

The registry is backed by a plain Python ``dict`` protected by a ``threading.Lock``
(safe for async FastAPI because writes happen on the event-loop thread and the
lock is acquired/released synchronously without blocking the loop for more
than a microsecond).

Persistence layer
-----------------
The current implementation is intentionally ephemeral: the registry is
pre-seeded with demo agents on startup and resets when the process restarts.
To wire in a real database (Postgres / Cosmos DB / Redis), replace
``_REGISTRY`` with async calls to your persistence layer and remove the lock
(async DB clients handle their own connection safety).

Agent self-registration
-----------------------
Agents call ``POST /api/v1/agents`` on startup with their name, model, and
optional tags.  They receive back the full ``Agent`` object including the
assigned ``id``.  They should subsequently call
``PATCH /api/v1/agents/{id}/heartbeat`` on a regular interval to keep
``last_seen`` fresh and update their operational stats.
"""

from __future__ import annotations

import threading
import uuid
from datetime import datetime, timezone

import structlog

from app.models.agent import (
    Agent,
    AgentHealth,
    AgentHeartbeat,
    AgentRegistration,
    AgentStatus,
)

_log = structlog.get_logger("agent_service")
_lock = threading.Lock()

# -----------------------------------------------------------------------
# Seed data — replaced/supplemented by live registrations at runtime
# -----------------------------------------------------------------------
_REGISTRY: dict[str, Agent] = {
    "agent-001": Agent(
        id="agent-001",
        name="research-agent",
        model="gpt-4o",
        status=AgentStatus.HEALTHY,
        uptime_seconds=86400,
        task_success_rate=0.98,
        tasks_per_minute=4.2,
        last_seen=datetime.now(tz=timezone.utc),
        registered_at=datetime.now(tz=timezone.utc),
        tags={"team": "research", "env": "production"},
    ),
    "agent-002": Agent(
        id="agent-002",
        name="summarizer-agent",
        model="gpt-4o-mini",
        status=AgentStatus.DEGRADED,
        uptime_seconds=3600,
        task_success_rate=0.87,
        tasks_per_minute=12.5,
        last_seen=datetime.now(tz=timezone.utc),
        registered_at=datetime.now(tz=timezone.utc),
        tags={"team": "content", "env": "production"},
    ),
    "agent-003": Agent(
        id="agent-003",
        name="embedding-indexer",
        model="text-embedding-3-large",
        status=AgentStatus.HEALTHY,
        uptime_seconds=172800,
        task_success_rate=0.999,
        tasks_per_minute=60.0,
        last_seen=datetime.now(tz=timezone.utc),
        registered_at=datetime.now(tz=timezone.utc),
        tags={"team": "platform", "env": "production"},
    ),
}


# -----------------------------------------------------------------------
# Read operations
# -----------------------------------------------------------------------


def list_agents() -> list[Agent]:
    """Return all registered agents (snapshot)."""
    with _lock:
        return list(_REGISTRY.values())


def get_agent(agent_id: str) -> Agent | None:
    """Look up a single agent by ID."""
    with _lock:
        return _REGISTRY.get(agent_id)


def get_agent_health(agent_id: str) -> AgentHealth | None:
    """Return a health snapshot for the given agent ID."""
    agent = get_agent(agent_id)
    if not agent:
        return None
    return AgentHealth(
        agent_id=agent.id,
        status=agent.status,
        latency_ms=85.0 if agent.status == AgentStatus.HEALTHY else 950.0,
        error_rate=1.0 - agent.task_success_rate,
        checked_at=datetime.now(tz=timezone.utc),
    )


# -----------------------------------------------------------------------
# Write operations
# -----------------------------------------------------------------------


def register_agent(registration: AgentRegistration) -> Agent:
    """Register a new agent (or update an existing one with the same ID).

    If ``registration.agent_id`` is provided and already exists, the record is
    updated in place (idempotent re-registration).  Otherwise a new UUID-based
    ID is assigned.
    """
    now = datetime.now(tz=timezone.utc)
    with _lock:
        agent_id = registration.agent_id or str(uuid.uuid4())
        existing = _REGISTRY.get(agent_id)
        agent = Agent(
            id=agent_id,
            name=registration.name,
            model=registration.model,
            status=AgentStatus.HEALTHY,
            uptime_seconds=0,
            task_success_rate=1.0,
            tasks_per_minute=0.0,
            last_seen=now,
            registered_at=existing.registered_at if existing else now,
            tags=registration.tags,
        )
        _REGISTRY[agent_id] = agent
        _log.info("agent.registered", agent_id=agent_id, name=registration.name)
    return agent


def deregister_agent(agent_id: str) -> bool:
    """Remove an agent from the registry.  Returns ``True`` if it existed."""
    with _lock:
        if agent_id not in _REGISTRY:
            return False
        del _REGISTRY[agent_id]
        _log.info("agent.deregistered", agent_id=agent_id)
    return True


def heartbeat_agent(agent_id: str, beat: AgentHeartbeat) -> Agent | None:
    """Update an agent's operational stats from a heartbeat payload.

    Returns the updated ``Agent`` or ``None`` if the agent is not registered.
    """
    now = datetime.now(tz=timezone.utc)
    with _lock:
        agent = _REGISTRY.get(agent_id)
        if not agent:
            return None
        updated = agent.model_copy(
            update={
                "status": beat.status,
                "last_seen": now,
                **(
                    {"task_success_rate": beat.task_success_rate}
                    if beat.task_success_rate is not None
                    else {}
                ),
                **(
                    {"tasks_per_minute": beat.tasks_per_minute}
                    if beat.tasks_per_minute is not None
                    else {}
                ),
                **(
                    {"uptime_seconds": beat.uptime_seconds}
                    if beat.uptime_seconds is not None
                    else {}
                ),
            }
        )
        _REGISTRY[agent_id] = updated
        _log.debug("agent.heartbeat", agent_id=agent_id, status=beat.status)
    return updated
