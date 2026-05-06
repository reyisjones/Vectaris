"""Background scheduler for periodic alert evaluation and webhook delivery.

Uses APScheduler's ``AsyncIOScheduler`` so it shares the FastAPI event loop.
Start it from the ``lifespan`` context manager; it will shut itself down when
the app stops.

Webhook delivery
----------------
Set ``ALERT_WEBHOOK_URL`` (+ optional ``ALERT_WEBHOOK_SECRET``) in the
environment.  On each evaluation cycle any *triggered* alert is POSTed as JSON
to that URL.  A SHA-256 HMAC of the raw JSON body is included in the
``X-Vectaris-Signature`` header when a secret is configured.

Scheduling
----------
``ALERT_EVAL_INTERVAL_SECONDS`` controls how often evaluation runs (default 60 s).
``ALERT_WEBHOOK_TIMEOUT_SECONDS`` controls the per-request HTTP timeout (default 5 s).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging

import httpx
import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.config import settings
from app.services.alert_service import evaluate_alerts

logger = structlog.get_logger("scheduler")

_scheduler: AsyncIOScheduler | None = None


async def _run_alert_eval() -> None:
    alerts = await evaluate_alerts()
    triggered = [a for a in alerts if not a.resolved]
    if not triggered:
        return

    logger.info("scheduler.alerts.triggered", count=len(triggered))

    webhook_url = settings.alert_webhook_url
    if not webhook_url:
        return

    payload = json.dumps(
        [a.model_dump(mode="json") for a in triggered],
        default=str,
    ).encode()

    headers: dict[str, str] = {"Content-Type": "application/json"}
    secret = settings.alert_webhook_secret
    if secret:
        sig = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        headers["X-Vectaris-Signature"] = f"sha256={sig}"

    try:
        async with httpx.AsyncClient(
            timeout=settings.alert_webhook_timeout_seconds
        ) as client:
            resp = await client.post(webhook_url, content=payload, headers=headers)
            resp.raise_for_status()
        logger.info("scheduler.webhook.delivered", status=resp.status_code)
    except Exception as exc:  # noqa: BLE001
        logger.warning("scheduler.webhook.failed", error=str(exc))


def start_scheduler() -> None:
    """Start the background scheduler.  Safe to call multiple times."""
    global _scheduler
    if _scheduler and _scheduler.running:
        return

    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(
        _run_alert_eval,
        trigger=IntervalTrigger(seconds=settings.alert_eval_interval_seconds),
        id="alert-eval",
        replace_existing=True,
        misfire_grace_time=30,
    )
    _scheduler.start()
    logger.info(
        "scheduler.started",
        interval_seconds=settings.alert_eval_interval_seconds,
        webhook_enabled=bool(settings.alert_webhook_url),
    )


def stop_scheduler() -> None:
    """Gracefully shut down the scheduler."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("scheduler.stopped")
