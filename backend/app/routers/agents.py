from fastapi import APIRouter, HTTPException

from app.models.agent import Agent, AgentHealth
from app.services.agent_service import get_agent_health, list_agents

router = APIRouter()


@router.get("", response_model=list[Agent])
def get_agents() -> list[Agent]:
    """List all registered agents with current status."""
    return list_agents()


@router.get("/{agent_id}/health", response_model=AgentHealth)
def agent_health(agent_id: str) -> AgentHealth:
    """Run a health check for a specific agent."""
    health = get_agent_health(agent_id)
    if not health:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    return health
