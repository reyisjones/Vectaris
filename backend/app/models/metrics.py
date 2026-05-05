from datetime import datetime

from pydantic import BaseModel, Field


class UsageMetric(BaseModel):
    timestamp: datetime
    model: str
    total_requests: int = Field(ge=0)
    total_tokens: int = Field(ge=0)
    error_count: int = Field(ge=0)
    error_rate: float = Field(ge=0.0, le=1.0)


class LatencyMetric(BaseModel):
    timestamp: datetime
    model: str
    p50_ms: float = Field(ge=0)
    p95_ms: float = Field(ge=0)
    p99_ms: float = Field(ge=0)


class UsageSummary(BaseModel):
    total_requests: int
    total_tokens: int
    error_rate: float
    models: list[UsageMetric]
    data_source: str = "stub"


class LatencySummary(BaseModel):
    models: list[LatencyMetric]
    data_source: str = "stub"
