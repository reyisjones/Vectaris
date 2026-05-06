import { useQuery } from "@tanstack/react-query";
import React, { useState } from "react";
import { CostBreakdown } from "../components/CostBreakdown";
import { ErrorCard, LoadingCard } from "../components/LoadingState";
import { MetricCard } from "../components/MetricCard";
import { PageHeader } from "../components/PageHeader";
import { TimeRangeSelector, TimePeriod } from "../components/TimeRangeSelector";
import { getCostForecast, getCosts } from "../services/api";

const HORIZON_OPTIONS = [
  { days: 7, label: "7 days" },
  { days: 30, label: "30 days" },
  { days: 60, label: "60 days" },
  { days: 90, label: "90 days" },
];

export const CostsPage: React.FC = () => {
  const [period, setPeriod] = useState<TimePeriod>("30d");
  const [horizonDays, setHorizonDays] = useState(30);

  const summary = useQuery({
    queryKey: ["costs", period],
    queryFn: () => getCosts(period),
  });
  const forecast = useQuery({
    queryKey: ["cost-forecast", horizonDays],
    queryFn: () => getCostForecast(horizonDays),
  });

  return (
    <>
      <PageHeader
        title="Costs"
        subtitle="Cost attribution by model and team, plus forward projection"
        actions={<TimeRangeSelector value={period} onChange={setPeriod} />}
      />
      {(summary.isError || forecast.isError) && (
        <ErrorCard message="Failed to load cost data." />
      )}

      <div className="grid grid-kpi" style={{ marginBottom: "1.25rem" }}>
        <MetricCard
          title="Total Spend"
          value={`$${(summary.data?.total_usd ?? 0).toFixed(2)}`}
          subtitle={summary.data?.period}
        />
        <MetricCard
          title="Daily Run-rate"
          value={`$${(forecast.data?.daily_run_rate_usd ?? 0).toFixed(2)}`}
          subtitle="rolling average"
        />
        <MetricCard
          title={`Projected (${horizonDays}d)`}
          value={`$${(forecast.data?.projected_usd ?? 0).toFixed(2)}`}
          trend="neutral"
        />
      </div>

      {/* Forecast horizon picker */}
      <div style={{ marginBottom: "1rem", display: "flex", alignItems: "center", gap: "0.75rem" }}>
        <span style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>Forecast horizon:</span>
        {HORIZON_OPTIONS.map((opt) => (
          <button
            key={opt.days}
            onClick={() => setHorizonDays(opt.days)}
            style={{
              padding: "0.2rem 0.65rem",
              borderRadius: "0.35rem",
              border: "1px solid var(--border, #2e2e40)",
              cursor: "pointer",
              fontSize: "0.8rem",
              fontWeight: horizonDays === opt.days ? 600 : 400,
              background:
                horizonDays === opt.days
                  ? "var(--accent, #7c3aed)"
                  : "var(--surface-2, #1e1e2e)",
              color: horizonDays === opt.days ? "#fff" : "var(--text-muted)",
            }}
          >
            {opt.label}
          </button>
        ))}
      </div>

      <div className="grid grid-2">
        {summary.isLoading ? (
          <LoadingCard rows={5} />
        ) : (
          <CostBreakdown
            title="By Model"
            records={summary.data?.by_model ?? []}
            dimension="model"
          />
        )}
        {summary.isLoading ? (
          <LoadingCard rows={5} />
        ) : (
          <CostBreakdown
            title="By Team"
            records={summary.data?.by_team ?? []}
            dimension="team"
          />
        )}
      </div>
    </>
  );
};
