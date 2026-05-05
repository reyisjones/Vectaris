"""Structured JSON logging using structlog.

Emits one JSON object per log line with correlation IDs (request_id and
trace_id when an OpenTelemetry span is active) so logs can be joined to
traces in downstream observability backends.
"""

from __future__ import annotations

import logging
import sys

import structlog

from app.config import settings


def _add_trace_context(_logger, _method, event_dict):  # type: ignore[no-untyped-def]
    try:
        from opentelemetry import trace

        span = trace.get_current_span()
        if span is not None:
            ctx = span.get_span_context()
            if ctx.is_valid:
                event_dict.setdefault("trace_id", format(ctx.trace_id, "032x"))
                event_dict.setdefault("span_id", format(ctx.span_id, "016x"))
    except Exception:  # pragma: no cover - tracing optional
        pass
    return event_dict


def configure_logging() -> None:
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            _add_trace_context,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name) if name else structlog.get_logger()
