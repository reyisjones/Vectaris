from fastapi import APIRouter, Query

from app.models.cost import CostForecast, CostSummary
from app.services.cost_service import forecast_costs, get_cost_summary

router = APIRouter()


@router.get("", response_model=CostSummary)
async def cost_summary(period: str = Query(default="30d", pattern=r"^\d+[dw]$")) -> CostSummary:
    """Cost breakdown by model and team for the specified period."""
    return await get_cost_summary(period=period)


@router.get("/forecast", response_model=CostForecast)
async def cost_forecast(
    horizon_days: int = Query(default=30, ge=1, le=365),
) -> CostForecast:
    """Naive linear projection of spend over a given horizon."""
    return await forecast_costs(horizon_days=horizon_days)
