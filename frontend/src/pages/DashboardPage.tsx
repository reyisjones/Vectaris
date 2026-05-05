import { useQuery } from "@tanstack/react-query";
import React from "react";
import { AgentHealthTable } from "../components/AgentHealthTable";
import { AlertsList } from "../components/AlertsList";
import { LatencyChart } from "../components/LatencyChart";
import { ErrorCard, LoadingCard } from "../components/LoadingState";
import { MetricCard } from "../components/MetricCard";
import { PageHeader } from "../components/PageHeader";
import {
  getAgents,
  getAlerts,
  getCosts,
  getLatencyMetrics,
  getUsageMetrics,
} from "../services/api";

const REFRESH_MS = 30_000;

export const DashboardPage: React.FC = () => {
  const usage = useQuery({
    queryKey: ["usage"],
    queryFn: getUsageMetrics,
    refetchInterval: REFRESH_MS,
  });
  const latency = useQuery({
    queryKey: ["latency"],
    queryFn: getLatencyMetrics,
    refetchInterval: REFRESH_MS,
  });
  const agents = useQuery({
    queryKey: ["agents"],
    queryFn: getAgents,
    refetchInterval: REFRESH_MS,
  });
  const costs = useQuery({
    queryKey: ["costs", "30d"],
    queryFn: () => getCosts("30d"),
  });
  const alerts = useQuery({
    queryKey: ["alerts"],
    queryFn: getAlerts,
    refetchInterval: 15_000,
  });

  const errored =
    usage.isError || latency.isError || agents.isError || costs.isError || alerts.isError;

  return (
    <>
      <PageHeader
        title="Overview"
        subtitle={`Live AI platform telemetry · refreshing every ${REFRESH_MS / 1000}s`}
      />
      {errored && <ErrorCard message="One or more telemetry sources failed to load." />}

      <div className="grid grid-kpi" style={{ marginBottom: "1.25rem" }}>
        <MetricCard
          title="Total Requests"
          value={(usage.data?.total_requests ?? 0).toLocaleString()}
          subtitle="last 30d"
          trend="up"
          trendValue="+12% vs prior period"
        />
        <MetricCard
          title="Total Tokens"
          value={(usage.data?.total_tokens ?? 0).toLocaleString()}
          subtitle="last 30d"
        />
        <MetricCard
          title="Error Rate"
          value={`${((usage.data?.error_rate ?? 0) * 100).toFixed(2)}%`}
          trend={(usage.data?.error_rate ?? 0) < 0.01 ? "up" : "down"}
        />
        <MetricCard
          title="Monthly Cost"
          value={`$${(costs.data?.total_usd ?? 0).toFixed(2)}`}
          subtitle={costs.data?.period}
        />
        <MetricCard
          title="Active Alerts"
          value={alerts.data?.length ?? 0}
          trend={alerts.data && alerts.data.length > 0 ? "down" : "up"}
        />
      </div>

      <div className="grid grid-2" style={{ marginBottom: "1.25rem" }}>
        {latency.isLoading ? (
          <LoadingCard rows={5} />
        ) : latency.data ? (
          <LatencyChart data={latency.data.models} />
        ) : null}
        {alerts.isLoading ? (
          <LoadingCard rows={4} />
        ) : (
          <AlertsList alerts={alerts.data ?? []} />
        )}
      </div>

      {agents.isLoading ? (
        <LoadingCard rows={4} />
      ) : (
        <AgentHealthTable agents={agents.data ?? []} />
      )}
    </>
  );
};
