"""OpenAI billing/usage adapter.

Fetches usage and cost data from the OpenAI API.  Two endpoints are used:

* ``GET /v1/usage`` — daily token + request counts per model (requires
  ``openai`` API key with org-level usage read access).
* ``GET /v1/dashboard/billing/usage`` — raw cost in cents (legacy dashboard API).

Configuration
-------------
``OPENAI_API_KEY`` — Your OpenAI API key.  Leave empty to fall back to stubs.
``OPENAI_ORG_ID``  — Optional organisation ID header (``OpenAI-Organization``).

Notes
-----
* The `/v1/dashboard/billing/usage` endpoint requires a *session API key* from
  the OpenAI dashboard (``sess-…``), not a standard project key.  If you only
  have a project key, only the `/v1/usage` token counts will be available;
  cost will be estimated from a hard-coded price table.
* OpenAI updates usage data with ~24 h delay — do not rely on this for real-
  time cost alerting.
"""

from __future__ import annotations

from datetime import date, timedelta

import structlog

from app.config import settings

_log = structlog.get_logger("adapter.openai_billing")

# Approximate cost per 1 M tokens (input + output blended) in USD.
# Update these when OpenAI changes pricing.
_PRICE_PER_M_TOKENS: dict[str, float] = {
    "gpt-4o": 7.50,
    "gpt-4o-mini": 0.30,
    "gpt-4-turbo": 15.00,
    "gpt-3.5-turbo": 0.60,
    "text-embedding-3-large": 0.13,
    "text-embedding-3-small": 0.02,
    "text-embedding-ada-002": 0.10,
}
_DEFAULT_PRICE_PER_M = 5.00  # fallback for unknown models


def _price_for(model: str) -> float:
    for prefix, price in _PRICE_PER_M_TOKENS.items():
        if model.startswith(prefix):
            return price
    return _DEFAULT_PRICE_PER_M


def _is_configured() -> bool:
    return bool(settings.openai_api_key)


def _headers() -> dict[str, str]:
    h = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }
    if settings.openai_org_id:
        h["OpenAI-Organization"] = settings.openai_org_id
    return h


async def get_usage_costs(period_days: int = 30) -> list[dict] | None:
    """Return per-model usage and estimated costs for the last ``period_days`` days.

    Each item in the returned list has:
    ``model``, ``token_count``, ``request_count``, ``usd_cost`` (estimated).

    Returns ``None`` when the adapter is not configured or the API call fails.
    """
    if not _is_configured():
        _log.debug("adapter.openai_billing.unavailable", reason="OPENAI_API_KEY not set")
        return None

    import httpx

    end = date.today()
    start = end - timedelta(days=period_days)

    url = "https://api.openai.com/v1/usage"
    params = {
        "date": start.isoformat(),  # The API accepts a start date
    }

    try:
        async with httpx.AsyncClient(timeout=20.0, headers=_headers()) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:  # noqa: BLE001
        _log.warning("adapter.openai_billing.error", error=str(exc))
        return None

    # Aggregate by model snapshot_id (which encodes the model name).
    by_model: dict[str, dict] = {}
    for day_entry in data.get("data", []):
        for item in day_entry.get("aggregation_timestamp", []) or [day_entry]:
            model_raw = item.get("snapshot_id") or item.get("model") or "unknown"
            # Normalise: "gpt-4o-2024-11-20" → "gpt-4o"
            model = _normalise_model(model_raw)
            tokens = int(item.get("n_context_tokens_total", 0)) + int(
                item.get("n_generated_tokens_total", 0)
            )
            requests = int(item.get("n_requests", 0))
            if model not in by_model:
                by_model[model] = {"token_count": 0, "request_count": 0}
            by_model[model]["token_count"] += tokens
            by_model[model]["request_count"] += requests

    result = []
    for model, agg in sorted(by_model.items()):
        tokens = agg["token_count"]
        estimated_usd = round(_price_for(model) * tokens / 1_000_000, 4)
        result.append(
            {
                "model": model,
                "token_count": tokens,
                "request_count": agg["request_count"],
                "usd_cost": estimated_usd,
            }
        )
    _log.info("adapter.openai_billing.fetched", models=len(result), period_days=period_days)
    return result


def _normalise_model(raw: str) -> str:
    """Strip date suffixes like ``-2024-11-20`` from snapshot IDs."""
    import re

    return re.sub(r"-\d{4}-\d{2}-\d{2}$", "", raw)
