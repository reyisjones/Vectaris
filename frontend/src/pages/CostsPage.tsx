import { useQuery } from "@tanstack/react-query";
import React from "react";
import { CostBreakdown } from "../components/CostBreakdown";
import { ErrorCard, LoadingCard } from "../components/LoadingState";
import { MetricCard } from "../components/MetricCard";
import { PageHeader } from "../components/PageHeader";
import { getCostForecast, getCosts } from "../services/api";

export const CostsPage: React.FC = () => {
  const summary = useQuery({
    queryKey: ["costs", "30d"],
    queryFn: () => getCosts("30d"),
  });
  const forecast = useQuery({
    queryKey: ["cost-forecast", 30],
    queryFn: () => getCostForecast(30),
  });

  return (
    <>
      <PageHeader
        title="Costs"
        subtitle="Cost attribution by model and team, plus forward projection"
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
          title="Projected (30d)"
          value={`$${(forecast.data?.projected_usd ?? 0).toFixed(2)}`}
          trend="neutral"
        />
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
