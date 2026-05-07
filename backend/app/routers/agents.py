from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status

from app.models.agent import Agent, AgentHealth, AgentHeartbeat, AgentRegistration
from app.ratelimit import limiter
from app.services.agent_service import (
    deregister_agent,
    get_agent_health,
    heartbeat_agent,
    list_agents,
    register_agent,
)

router = APIRouter()


@router.get("", response_model=list[Agent])
def get_agents() -> list[Agent]:
    """List all registered agents with current status."""
    return list_agents()


@router.post("", response_model=Agent, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")  # Prevent agent registration spam
def create_agent(request: Request, registration: AgentRegistration) -> Agent:
    """Register a new agent (or idempotently re-register an existing one).

    On success the full ``Agent`` record is returned including the assigned
    ``id``.  Agents should subsequently call the heartbeat endpoint to keep
    their ``last_seen`` timestamp fresh.
    """
    return register_agent(registration)


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_agent(agent_id: str) -> None:
    """Deregister an agent by ID."""
    if not deregister_agent(agent_id):
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")


@router.patch("/{agent_id}/heartbeat", response_model=Agent)
def agent_heartbeat(agent_id: str, beat: AgentHeartbeat) -> Agent:
    """Accept a heartbeat from a running agent to refresh its stats."""
    agent = heartbeat_agent(agent_id, beat)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    return agent


@router.get("/{agent_id}/health", response_model=AgentHealth)
def agent_health(agent_id: str) -> AgentHealth:
    """Return a health snapshot for a specific agent."""
    health = get_agent_health(agent_id)
    if not health:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    return health
