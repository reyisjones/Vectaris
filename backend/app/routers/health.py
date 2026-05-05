from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel

from app.config import settings

router = APIRouter(tags=["system"])


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str


@router.get("/health", response_model=HealthResponse)
def liveness() -> HealthResponse:
    """Kubernetes liveness probe endpoint."""
    return HealthResponse(
        status="ok",
        version=settings.api_version,
        environment=settings.environment,
    )


@router.get("/ready", response_model=HealthResponse)
def readiness() -> HealthResponse:
    """Kubernetes readiness probe endpoint."""
    return HealthResponse(
        status="ready",
        version=settings.api_version,
        environment=settings.environment,
    )


@router.get("/metrics")
def prometheus_metrics() -> Response:
    """Prometheus-format metrics scrape endpoint."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
