from datetime import datetime

from pydantic import BaseModel, Field


class CostRecord(BaseModel):
    model: str
    team: str
    usd_cost: float = Field(ge=0)
    token_count: int = Field(ge=0)
    request_count: int = Field(ge=0)


class CostSummary(BaseModel):
    total_usd: float
    period: str
    by_model: list[CostRecord]
    by_team: list[CostRecord]


class CostForecast(BaseModel):
    horizon_days: int
    projected_usd: float
    daily_run_rate_usd: float
    generated_at: datetime
