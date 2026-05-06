import { useQuery } from "@tanstack/react-query";
import React, { useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ErrorCard, LoadingCard } from "../components/LoadingState";
import { MetricCard } from "../components/MetricCard";
import { PageHeader } from "../components/PageHeader";
import { TimeRangeSelector, TimePeriod } from "../components/TimeRangeSelector";
import { axisStroke, gridStroke, tooltipStyle } from "../components/chartTheme";
import { getLatencyMetrics, getUsageMetrics } from "../services/api";

export const ModelPage: React.FC = () => {
  const { modelName } = useParams<{ modelName: string }>();
  const [period, setPeriod] = useState<TimePeriod>("30d");

  const latency = useQuery({
    queryKey: ["latency", period],
    queryFn: getLatencyMetrics,
    refetchInterval: 30_000,
  });

  const usage = useQuery({
    queryKey: ["usage", period],
    queryFn: getUsageMetrics,
    refetchInterval: 30_000,
  });

  const modelLatency = latency.data?.models.find((m) => m.model === modelName);
  const modelUsage = usage.data?.models.find((m) => m.model === modelName);

  // Build a small sparkline dataset from whatever snapshots we have
  const latencyHistory = latency.data?.models
    .filter((m) => m.model === modelName)
    .map((m) => ({
      label: new Date(m.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      p50: m.p50_ms,
      p95: m.p95_ms,
      p99: m.p99_ms,
    })) ?? [];

  const errorHistory = usage.data?.models
    .filter((m) => m.model === modelName)
    .map((m) => ({
      label: new Date(m.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      error_rate: +(m.error_rate * 100).toFixed(3),
      requests: m.total_requests,
    })) ?? [];

  return (
    <>
      <PageHeader
        title={modelName ?? "Model"}
        subtitle="Per-model latency history and error timeline"
        actions={<TimeRangeSelector value={period} onChange={setPeriod} />}
      />

      <div style={{ marginBottom: "0.75rem" }}>
        <Link to="/" style={{ color: "var(--accent)", fontSize: "0.85rem" }}>
          ← Back to Dashboard
        </Link>
      </div>

      {(latency.isError || usage.isError) && (
        <ErrorCard message="Failed to load model metrics." />
      )}

      <div className="grid grid-kpi" style={{ marginBottom: "1.25rem" }}>
        <MetricCard
          title="P50 Latency"
          value={modelLatency ? `${modelLatency.p50_ms.toFixed(0)}ms` : "—"}
          subtitle={`last ${period}`}
        />
        <MetricCard
          title="P95 Latency"
          value={modelLatency ? `${modelLatency.p95_ms.toFixed(0)}ms` : "—"}
          subtitle={`last ${period}`}
        />
        <MetricCard
          title="P99 Latency"
          value={modelLatency ? `${modelLatency.p99_ms.toFixed(0)}ms` : "—"}
          subtitle={`last ${period}`}
          trend={
            modelLatency && modelLatency.p99_ms > 1000 ? "down" : "up"
          }
        />
        <MetricCard
          title="Error Rate"
          value={modelUsage ? `${(modelUsage.error_rate * 100).toFixed(2)}%` : "—"}
          trend={modelUsage && modelUsage.error_rate > 0.02 ? "down" : "up"}
        />
        <MetricCard
          title="Total Requests"
          value={(modelUsage?.total_requests ?? 0).toLocaleString()}
          subtitle={`last ${period}`}
        />
        <MetricCard
          title="Total Tokens"
          value={(modelUsage?.total_tokens ?? 0).toLocaleString()}
          subtitle={`last ${period}`}
        />
      </div>

      <div className="grid grid-2" style={{ marginBottom: "1.25rem" }}>
        {latency.isLoading ? (
          <LoadingCard rows={5} />
        ) : (
          <div className="card">
            <p className="card-title">Latency History (ms)</p>
            {latencyHistory.length === 0 ? (
              <p style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
                No history available — metrics are aggregated as snapshots arrive.
              </p>
            ) : (
              <ResponsiveContainer width="100%" height={240}>
                <LineChart data={latencyHistory}>
                  <CartesianGrid strokeDasharray="3 3" stroke={gridStroke()} />
                  <XAxis dataKey="label" stroke={axisStroke()} tick={{ fontSize: 11 }} />
                  <YAxis stroke={axisStroke()} tick={{ fontSize: 11 }} unit="ms" />
                  <Tooltip contentStyle={tooltipStyle()} />
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                  <Line type="monotone" dataKey="p50" name="P50" stroke="var(--accent)" dot={false} />
                  <Line type="monotone" dataKey="p95" name="P95" stroke="var(--warn)" dot={false} />
                  <Line type="monotone" dataKey="p99" name="P99" stroke="var(--danger)" dot={false} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        )}

        {usage.isLoading ? (
          <LoadingCard rows={5} />
        ) : (
          <div className="card">
            <p className="card-title">Error Rate Timeline (%)</p>
            {errorHistory.length === 0 ? (
              <p style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
                No history available — metrics are aggregated as snapshots arrive.
              </p>
            ) : (
              <ResponsiveContainer width="100%" height={240}>
                <LineChart data={errorHistory}>
                  <CartesianGrid strokeDasharray="3 3" stroke={gridStroke()} />
                  <XAxis dataKey="label" stroke={axisStroke()} tick={{ fontSize: 11 }} />
                  <YAxis stroke={axisStroke()} tick={{ fontSize: 11 }} unit="%" />
                  <Tooltip contentStyle={tooltipStyle()} />
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                  <Line
                    type="monotone"
                    dataKey="error_rate"
                    name="Error Rate"
                    stroke="var(--danger)"
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        )}
      </div>
    </>
  );
};
