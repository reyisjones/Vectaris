from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class Agent(BaseModel):
    id: str
    name: str
    model: str
    status: AgentStatus
    uptime_seconds: int
    task_success_rate: float
    tasks_per_minute: float
    last_seen: datetime
    registered_at: datetime
    tags: dict[str, str] = Field(default_factory=dict)


class AgentRegistration(BaseModel):
    """Request body for ``POST /api/v1/agents``."""

    name: str = Field(..., min_length=1, max_length=128, description="Human-readable agent name")
    model: str = Field(..., min_length=1, max_length=128, description="LLM model used by the agent")
    tags: dict[str, str] = Field(default_factory=dict, description="Arbitrary key-value metadata")
    agent_id: Optional[str] = Field(
        None,
        description="Caller-supplied stable ID (e.g. pod name). Auto-generated if omitted.",
    )


class AgentHeartbeat(BaseModel):
    """Request body for ``PATCH /api/v1/agents/{agent_id}/heartbeat``."""

    status: AgentStatus = AgentStatus.HEALTHY
    task_success_rate: Optional[float] = None
    tasks_per_minute: Optional[float] = None
    uptime_seconds: Optional[int] = None


class AgentHealth(BaseModel):
    agent_id: str
    status: AgentStatus
    latency_ms: float
    error_rate: float
    checked_at: datetime
