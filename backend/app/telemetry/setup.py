"""OpenTelemetry tracing + metrics configuration.

Telemetry is disabled by default; set OTEL_ENABLED=true to activate the OTLP
exporter. The FastAPI instrumentor is attached lazily inside `instrument_app`
so it can be invoked after the application object exists.
"""

from __future__ import annotations

import structlog

from app.config import settings

_log = structlog.get_logger("telemetry")
_configured = False


def configure_telemetry() -> None:
    """Configure global tracer + meter providers (idempotent)."""
    global _configured
    if _configured or not settings.otel_enabled:
        return

    from opentelemetry import metrics, trace
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
        OTLPMetricExporter,
    )
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    resource = Resource.create(
        {
            "service.name": settings.otel_service_name,
            "deployment.environment": settings.environment,
            "service.version": settings.api_version,
        }
    )

    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(
        BatchSpanProcessor(
            OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint)
        )
    )
    trace.set_tracer_provider(tracer_provider)

    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=settings.otel_exporter_otlp_endpoint)
    )
    metrics.set_meter_provider(
        MeterProvider(resource=resource, metric_readers=[metric_reader])
    )

    _configured = True
    _log.info(
        "telemetry.configured",
        endpoint=settings.otel_exporter_otlp_endpoint,
        service=settings.otel_service_name,
    )


def instrument_app(app) -> None:  # type: ignore[no-untyped-def]
    """Attach FastAPI + httpx auto-instrumentation if telemetry is enabled."""
    if not settings.otel_enabled:
        return
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

    FastAPIInstrumentor.instrument_app(app)
    HTTPXClientInstrumentor().instrument()
