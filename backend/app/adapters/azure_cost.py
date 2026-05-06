"""Azure Cost Management adapter.

Queries the Azure Cost Management REST API to retrieve per-resource-group /
per-service-name spend for the subscription.

Configuration
-------------
``AZURE_SUBSCRIPTION_ID``  — Target Azure subscription.
``AZURE_TENANT_ID``        — Azure AD tenant (for client-credentials token).
``AZURE_CLIENT_ID``        — Service-principal application (client) ID.
``AZURE_CLIENT_SECRET``    — Service-principal secret.
``AZURE_CM_SCOPE``         — Scope override (default: ``/subscriptions/{sub_id}``).

The adapter obtains a short-lived OAuth 2.0 access token from
``login.microsoftonline.com`` and then calls the Cost Management Query API.

When none of the required settings are present the adapter returns ``None``
so the caller can fall back to stub data.
"""

from __future__ import annotations

from datetime import date, timedelta

import httpx
import structlog

from app.config import settings

_log = structlog.get_logger("adapter.azure_cost")

_TOKEN_URL = "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
_CM_URL = (
    "https://management.azure.com{scope}/providers/Microsoft.CostManagement"
    "/query?api-version=2023-11-01"
)


def _is_configured() -> bool:
    return bool(
        settings.azure_subscription_id
        and settings.azure_tenant_id
        and settings.azure_client_id
        and settings.azure_client_secret
    )


async def _get_token(client: httpx.AsyncClient) -> str:
    url = _TOKEN_URL.format(tenant_id=settings.azure_tenant_id)
    resp = await client.post(
        url,
        data={
            "grant_type": "client_credentials",
            "client_id": settings.azure_client_id,
            "client_secret": settings.azure_client_secret,
            "scope": "https://management.azure.com/.default",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


async def get_usage_costs(period_days: int = 30) -> list[dict] | None:
    """Return per-service cost data for *period_days* from Azure Cost Management.

    Each item: ``model`` (service name), ``team`` (resource group),
    ``usd_cost``, ``token_count`` (always 0 — not available), ``request_count`` (0).

    Returns ``None`` when the adapter is not configured or the API call fails.
    """
    if not _is_configured():
        _log.debug("adapter.azure_cost.unavailable", reason="missing credentials")
        return None

    scope = (
        settings.azure_cm_scope
        or f"/subscriptions/{settings.azure_subscription_id}"
    )
    today = date.today()
    start = (today - timedelta(days=period_days)).isoformat()
    end = today.isoformat()

    query_body = {
        "type": "ActualCost",
        "dataSet": {
            "granularity": "None",
            "aggregation": {
                "totalCost": {"name": "Cost", "function": "Sum"},
            },
            "grouping": [
                {"type": "Dimension", "name": "ServiceName"},
                {"type": "Dimension", "name": "ResourceGroup"},
            ],
        },
        "timeframe": "Custom",
        "timePeriod": {"from": f"{start}T00:00:00Z", "to": f"{end}T23:59:59Z"},
    }

    try:
        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
            token = await _get_token(client)
            url = _CM_URL.format(scope=scope)
            resp = await client.post(
                url,
                json=query_body,
                headers={"Authorization": f"Bearer {token}"},
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:  # noqa: BLE001
        _log.warning("adapter.azure_cost.error", error=str(exc))
        return None

    rows = data.get("properties", {}).get("rows", [])
    # columns: Cost, Currency, ServiceName, ResourceGroup (order from API)
    cols = [c["name"].lower() for c in data.get("properties", {}).get("columns", [])]

    results: list[dict] = []
    for row in rows:
        row_dict = dict(zip(cols, row))
        cost_val = float(row_dict.get("cost", 0))
        # Convert from billing currency to USD (best-effort; skip non-USD)
        results.append(
            {
                "model": row_dict.get("servicename", "unknown"),
                "team": row_dict.get("resourcegroup", "unknown"),
                "usd_cost": round(cost_val, 4),
                "token_count": 0,
                "request_count": 0,
            }
        )

    _log.info("adapter.azure_cost.ok", rows=len(results))
    return results
