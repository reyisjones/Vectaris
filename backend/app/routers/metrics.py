from fastapi import APIRouter

from app.models.metrics import LatencySummary, UsageSummary
from app.services.metrics_service import get_latency_summary, get_usage_summary

router = APIRouter()


@router.get("/usage", response_model=UsageSummary)
async def usage_metrics() -> UsageSummary:
    """Aggregate token and request counts across all models."""
    return await get_usage_summary()


@router.get("/latency", response_model=LatencySummary)
async def latency_metrics() -> LatencySummary:
    """P50/P95/P99 latency per model."""
    return await get_latency_summary()
