import asyncio
import json

import structlog
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.models.metrics import LatencySummary, UsageSummary
from app.services.metrics_service import get_latency_summary, get_usage_summary

router = APIRouter()
_log = structlog.get_logger("metrics.sse")


@router.get("/usage", response_model=UsageSummary)
async def usage_metrics() -> UsageSummary:
    """Aggregate token and request counts across all models."""
    return await get_usage_summary()


@router.get("/latency", response_model=LatencySummary)
async def latency_metrics() -> LatencySummary:
    """P50/P95/P99 latency per model."""
    return await get_latency_summary()


@router.get(
    "/stream",
    summary="SSE live metrics stream",
    response_class=StreamingResponse,
    responses={200: {"content": {"text/event-stream": {}}}},
)
async def stream_metrics(request: Request, interval: int = 5):
    """Server-Sent Events endpoint that pushes combined usage + latency metrics.

    Clients should connect with ``EventSource('/api/v1/metrics/stream')``.
    Each event is a JSON object: ``{ usage, latency, timestamp }``.
    The stream closes automatically when the client disconnects.

    Query params:
        interval: push interval in seconds (default 5, min 2, max 60)
    """
    push_interval = max(2, min(60, interval))

    async def event_generator():
        _log.info("metrics.stream.connected", interval=push_interval)
        try:
            while True:
                if await request.is_disconnected():
                    _log.info("metrics.stream.disconnected")
                    break

                usage = await get_usage_summary()
                latency = await get_latency_summary()

                payload = {
                    "usage": usage.model_dump(),
                    "latency": latency.model_dump(),
                }

                # SSE format: "data: <json>\n\n"
                yield f"data: {json.dumps(payload, default=str)}\n\n"
                await asyncio.sleep(push_interval)
        except asyncio.CancelledError:
            _log.info("metrics.stream.cancelled")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disable nginx buffering for SSE
        },
    )
