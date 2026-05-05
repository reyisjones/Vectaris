from datetime import datetime, timezone

from app.models.cost import CostForecast, CostRecord, CostSummary


def _records() -> list[CostRecord]:
    return [
        CostRecord(
            model="gpt-4o",
            team="platform",
            usd_cost=412.50,
            token_count=1_650_000,
            request_count=3_200,
        ),
        CostRecord(
            model="gpt-4o-mini",
            team="search",
            usd_cost=28.90,
            token_count=9_633_000,
            request_count=48_000,
        ),
        CostRecord(
            model="text-embedding-3-large",
            team="indexing",
            usd_cost=18.20,
            token_count=91_000_000,
            request_count=180_000,
        ),
        CostRecord(
            model="llama3:8b",
            team="research",
            usd_cost=0.0,
            token_count=12_400_000,
            request_count=22_000,
        ),
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


def get_cost_summary(period: str = "30d") -> CostSummary:
    records = _records()
    return CostSummary(
        total_usd=round(sum(r.usd_cost for r in records), 2),
        period=period,
        by_model=records,
        by_team=_aggregate_by_team(records),
    )


def _period_to_days(period: str) -> int:
    unit = period[-1]
    value = int(period[:-1])
    return value if unit == "d" else value * 7


def forecast_costs(horizon_days: int) -> CostForecast:
    summary = get_cost_summary()
    period_days = _period_to_days(summary.period) or 30
    daily_rate = summary.total_usd / period_days
    return CostForecast(
        horizon_days=horizon_days,
        projected_usd=round(daily_rate * horizon_days, 2),
        daily_run_rate_usd=round(daily_rate, 2),
        generated_at=datetime.now(tz=timezone.utc),
    )
