import React from "react";
import type { Agent } from "../services/api";

interface Props {
  agents: Agent[];
}

const badgeFor = (s: Agent["status"]) =>
  s === "healthy"
    ? "success"
    : s === "degraded"
      ? "warn"
      : s === "unhealthy"
        ? "danger"
        : "muted";

const formatUptime = (sec: number): string => {
  if (sec < 3600) return `${Math.floor(sec / 60)}m`;
  if (sec < 86400) return `${Math.floor(sec / 3600)}h`;
  return `${Math.floor(sec / 86400)}d`;
};

export const AgentHealthTable: React.FC<Props> = ({ agents }) => (
  <div className="card" style={{ overflowX: "auto" }}>
    <p className="card-title">Agent Health</p>
    <table>
      <thead>
        <tr>
          <th>Name</th>
          <th>Model</th>
          <th>Status</th>
          <th>Uptime</th>
          <th>Success Rate</th>
          <th>Tasks/min</th>
        </tr>
      </thead>
      <tbody>
        {agents.map((a) => (
          <tr key={a.id}>
            <td style={{ fontWeight: 500 }}>{a.name}</td>
            <td style={{ color: "var(--text-muted)" }}>{a.model}</td>
            <td>
              <span className={`badge ${badgeFor(a.status)}`}>{a.status}</span>
            </td>
            <td>{formatUptime(a.uptime_seconds)}</td>
            <td>{(a.task_success_rate * 100).toFixed(1)}%</td>
            <td>{a.tasks_per_minute}</td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);
