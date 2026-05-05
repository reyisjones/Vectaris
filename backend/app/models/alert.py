from datetime import datetime
from enum import Enum

from pydantic import BaseModel


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
