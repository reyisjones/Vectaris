"""FastAPI application factory.

Wires up logging, telemetry, middleware, exception handlers, and routers.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.auth import APIKeyMiddleware
from app.config import settings
from app.logging_config import configure_logging
from app.middleware import RequestContextMiddleware
from app.routers import agents, alerts, costs, health, llm, metrics
from app.scheduler import start_scheduler, stop_scheduler
from app.telemetry.setup import configure_telemetry, instrument_app


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    configure_telemetry()
    instrument_app(app)
    structlog.get_logger("app").info(
        "app.startup",
        environment=settings.environment,
        version=settings.api_version,
        otel_enabled=settings.otel_enabled,
        ollama_enabled=settings.ollama_enabled,
    )
    start_scheduler()
    yield
    stop_scheduler()
    structlog.get_logger("app").info("app.shutdown")


def create_app() -> FastAPI:
    configure_logging()

    app = FastAPI(
        title=settings.app_name,
        description="Observability API for AI usage, latency, cost, and agent health.",
        version=settings.api_version,
        lifespan=lifespan,
    )
    app.add_middleware(APIKeyMiddleware)
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(  # type: ignore[unused-ignore]
        request: Request, exc: Exception
    ) -> JSONResponse:
        structlog.get_logger("app").exception(
            "app.unhandled_exception", path=request.url.path
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    app.include_router(health.router)
    app.include_router(metrics.router, prefix="/api/v1/metrics", tags=["metrics"])
    app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])
    app.include_router(costs.router, prefix="/api/v1/costs", tags=["costs"])
    app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["alerts"])
    app.include_router(llm.router, prefix="/api/v1/llm", tags=["llm"])

    return app


app = create_app()
