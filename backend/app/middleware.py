"""HTTP middleware: request IDs, structured access logs, metric counters."""

from __future__ import annotations

import time
import uuid
from collections.abc import Awaitable, Callable

import structlog
from prometheus_client import Counter, Histogram
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

REQUEST_ID_HEADER = "X-Request-ID"

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests processed by the API.",
    ["method", "path", "status"],
)
http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds.",
    ["method", "path"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
)

_log = structlog.get_logger("http")


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attach a request ID, time the request, and emit a structured access log."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        structlog.contextvars.bind_contextvars(request_id=request_id)
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            duration = time.perf_counter() - start
            http_requests_total.labels(request.method, request.url.path, "500").inc()
            http_request_duration_seconds.labels(
                request.method, request.url.path
            ).observe(duration)
            _log.exception(
                "request.failed",
                method=request.method,
                path=request.url.path,
                duration_ms=round(duration * 1000, 2),
            )
            structlog.contextvars.clear_contextvars()
            raise

        duration = time.perf_counter() - start
        response.headers[REQUEST_ID_HEADER] = request_id
        http_requests_total.labels(
            request.method, request.url.path, str(response.status_code)
        ).inc()
        http_request_duration_seconds.labels(
            request.method, request.url.path
        ).observe(duration)
        _log.info(
            "request.completed",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=round(duration * 1000, 2),
        )
        structlog.contextvars.clear_contextvars()
        return response
