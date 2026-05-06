"""Cost service — queries cost adapters in priority order, falls back to stubs.

Data source priority
--------------------
1. **Azure Cost Management** — when ``AZURE_SUBSCRIPTION_ID`` + credentials set.
2. **AWS Cost Explorer**     — when ``AWS_ACCESS_KEY_ID`` + secret set.
3. **OpenAI billing API**    — when ``OPENAI_API_KEY`` is set.
4. **Stub**                  — deterministic demo data for dev / CI.

The ``data_source`` field in the response indicates which backend answered.
"""

from __future__ import annotations

import structlog
from datetime import datetime, timezone

from app.adapters.aws_cost import get_usage_costs as aws_get_costs
from app.adapters.azure_cost import get_usage_costs as azure_get_costs
from app.adapters.openai_billing import get_usage_costs as openai_get_costs
from app.models.cost import CostForecast, CostRecord, CostSummary

_log = structlog.get_logger("cost_service")


# ---------------------------------------------------------------------------
# Stub helpers
# ---------------------------------------------------------------------------


def _stub_records() -> list[CostRecord]:
    return [
        CostRecord(model="gpt-4o", team="platform", usd_cost=412.50, token_count=1_650_000, request_count=3_200),
        CostRecord(model="gpt-4o-mini", team="search", usd_cost=28.90, token_count=9_633_000, request_count=48_000),
        CostRecord(model="text-embedding-3-large", team="indexing", usd_cost=18.20, token_count=91_000_000, request_count=180_000),
        CostRecord(model="llama3:8b", team="research", usd_cost=0.0, token_count=12_400_000, request_count=22_000),
    ]


def _aggregate_by_team(records: list[CostRecord]) -> list[CostRecord]:
    teams: dict[str, CostRecord] = {}
    for r in records:
        existing = teams.get(r.team)
        if existing is None:
            teams[r.team] = r.model_copy(update={"model": "mixed"})
        else:
            teams[r.team] = existing.model_copy(
                update={
                    "usd_cost": round(existing.usd_cost + r.usd_cost, 2),
                    "token_count": existing.token_count + r.token_count,
                    "request_count": existing.request_count + r.request_count,
                }
            )
    return list(teams.values())


def _period_to_days(period: str) -> int:
    unit = period[-1]
    value = int(period[:-1])
    return value if unit == "d" else value * 7


async def _try_adapters(period_days: int) -> tuple[list[dict] | None, str]:
    """Try each adapter in priority order, returning (rows, source_name)."""
    rows = await azure_get_costs(period_days=period_days)
    if rows is not None:
        return rows, "azure"
    rows = await aws_get_costs(period_days=period_days)
    if rows is not None:
        return rows, "aws"
    rows = await openai_get_costs(period_days=period_days)
    if rows is not None:
        return rows, "openai"
    return None, "stub"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def get_cost_summary(period: str = "30d") -> CostSummary:
    """Return cost breakdown by model and team.  Tries adapters in priority order."""
    period_days = _period_to_days(period) or 30
    rows, source = await _try_adapters(period_days)

    if rows is None:
        _log.debug("cost.fallback_to_stub")
        records = _stub_records()
        return CostSummary(
            total_usd=round(sum(r.usd_cost for r in records), 2),
            period=period,
            by_model=records,
            by_team=_aggregate_by_team(records),
            data_source="stub",
        )

    records = [
        CostRecord(
            model=r["model"],
            team=r.get("team", source),
            usd_cost=r["usd_cost"],
            token_count=r.get("token_count", 0),
            request_count=r.get("request_count", 0),
        )
        for r in rows
    ]
    _log.info("cost.from_adapter", source=source, models=len(records))
    return CostSummary(
        total_usd=round(sum(r.usd_cost for r in records), 2),
        period=period,
        by_model=records,
        by_team=_aggregate_by_team(records),
        data_source=source,
    )


async def forecast_costs(horizon_days: int) -> CostForecast:
    """Project costs forward based on the current daily run rate."""
    summary = await get_cost_summary()
    period_days = _period_to_days(summary.period) or 30
    daily_rate = summary.total_usd / period_days
    return CostForecast(
        horizon_days=horizon_days,
        projected_usd=round(daily_rate * horizon_days, 2),
        daily_run_rate_usd=round(daily_rate, 2),
        generated_at=datetime.now(tz=timezone.utc),
        data_source=summary.data_source,
    )

