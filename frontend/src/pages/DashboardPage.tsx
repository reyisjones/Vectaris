import { useQuery } from "@tanstack/react-query";
import React, { useState } from "react";
import { AgentHealthTable } from "../components/AgentHealthTable";
import { AlertsList } from "../components/AlertsList";
import { LatencyChart } from "../components/LatencyChart";
import { ErrorCard, LoadingCard } from "../components/LoadingState";
import { MetricCard } from "../components/MetricCard";
import { PageHeader } from "../components/PageHeader";
import { TimeRangeSelector, TimePeriod } from "../components/TimeRangeSelector";
import { useMetricsStream } from "../hooks/useMetricsStream";
import {
  getAgents,
  getAlerts,
  getCosts,
} from "../services/api";

const REFRESH_MS = 30_000;

/** Small indicator dot showing SSE connection status */
const StreamBadge: React.FC<{ connected: boolean; lastUpdated: string | null }> = ({
  connected,
  lastUpdated,
}) => (
  <span
    title={
      connected
        ? `Live · last update ${lastUpdated ? new Date(lastUpdated).toLocaleTimeString() : "—"}`
        : "Connecting…"
    }
    style={{
      display: "inline-flex",
      alignItems: "center",
      gap: "0.35rem",
      fontSize: "0.75rem",
      color: connected ? "var(--success, #22c55e)" : "var(--text-muted)",
    }}
  >
    <span
      style={{
        width: 8,
        height: 8,
        borderRadius: "50%",
        background: connected ? "var(--success, #22c55e)" : "var(--text-muted)",
        boxShadow: connected ? "0 0 0 3px rgba(34,197,94,0.25)" : "none",
        display: "inline-block",
        animation: connected ? "pulse 2s infinite" : "none",
      }}
    />
    {connected ? "Live" : "Connecting…"}
  </span>
);

export const DashboardPage: React.FC = () => {
  const [period, setPeriod] = useState<TimePeriod>("30d");

  // Real-time metrics via SSE (replaces polling for usage + latency)
  const stream = useMetricsStream(5);

  const agents = useQuery({
    queryKey: ["agents"],
    queryFn: getAgents,
    refetchInterval: REFRESH_MS,
  });
  const costs = useQuery({
    queryKey: ["costs", period],
    queryFn: () => getCosts(period),
  });
  const alerts = useQuery({
    queryKey: ["alerts"],
    queryFn: getAlerts,
    refetchInterval: 15_000,
  });

  const errored = agents.isError || costs.isError || alerts.isError;

  return (
    <>
      <PageHeader
        title="Overview"
        subtitle="Live AI platform telemetry"
        actions={
          <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
            <StreamBadge connected={stream.connected} lastUpdated={stream.lastUpdated} />
            <TimeRangeSelector value={period} onChange={setPeriod} />
          </div>
        }
      />
      {errored && <ErrorCard message="One or more telemetry sources failed to load." />}
      {stream.error && (
        <ErrorCard message={stream.error} />
      )}

      <div className="grid grid-kpi" style={{ marginBottom: "1.25rem" }}>
        <MetricCard
          title="Total Requests"
          value={(stream.usage?.total_requests ?? 0).toLocaleString()}
          subtitle={`last ${period}`}
          trend="up"
          trendValue="+12% vs prior period"
        />
        <MetricCard
          title="Total Tokens"
          value={(stream.usage?.total_tokens ?? 0).toLocaleString()}
          subtitle={`last ${period}`}
        />
        <MetricCard
          title="Error Rate"
          value={`${((stream.usage?.error_rate ?? 0) * 100).toFixed(2)}%`}
          trend={(stream.usage?.error_rate ?? 0) < 0.01 ? "up" : "down"}
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
        {!stream.latency ? (
          <LoadingCard rows={5} />
        ) : (
          <LatencyChart data={stream.latency.models} />
        )}
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
