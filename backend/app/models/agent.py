from datetime import datetime
from enum import Enum

from pydantic import BaseModel


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


class AgentHealth(BaseModel):
    agent_id: str
    status: AgentStatus
    latency_ms: float
    error_rate: float
    checked_at: datetime
