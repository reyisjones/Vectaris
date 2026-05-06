from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class AlertSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Alert(BaseModel):
    id: str
    name: str
    severity: AlertSeverity
    message: str
    triggered_at: datetime
    resolved: bool = False
    source: str = "system"


# ---------------------------------------------------------------------------
# Alert rules
# ---------------------------------------------------------------------------

AlertMetric = Literal[
    "latency_p99_ms",
    "latency_p95_ms",
    "latency_p50_ms",
    "error_rate",
    "agent_task_success_rate",
    "cost_budget_pct",
]

AlertOperator = Literal[">", ">=", "<", "<=", "=="]


class AlertRule(BaseModel):
    id: str = Field(..., description="Unique rule identifier (slug)")
    name: str = Field(..., description="Human-readable rule name")
    metric: AlertMetric
    operator: AlertOperator = ">"
    threshold: float
    severity: AlertSeverity = AlertSeverity.MEDIUM
    source: str = "system"
    enabled: bool = True


class AlertRuleCreate(BaseModel):
    """Payload for creating / updating a rule via the API."""

    name: str
    metric: AlertMetric
    operator: AlertOperator = ">"
    threshold: float
    severity: AlertSeverity = AlertSeverity.MEDIUM
    source: str = "system"
    enabled: bool = True
