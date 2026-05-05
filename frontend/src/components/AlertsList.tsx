import React from "react";
import type { Alert } from "../services/api";

const severityClass: Record<Alert["severity"], string> = {
  critical: "danger",
  high: "danger",
  medium: "warn",
  low: "muted",
};

interface Props {
  alerts: Alert[];
}

export const AlertsList: React.FC<Props> = ({ alerts }) => {
  if (alerts.length === 0) {
    return (
      <div className="card">
        <p className="card-title">Active Alerts</p>
        <p style={{ color: "var(--text-muted)", margin: 0 }}>
          ✓ All systems nominal
        </p>
      </div>
    );
  }
  return (
    <div className="card">
      <p className="card-title">Active Alerts ({alerts.length})</p>
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {alerts.map((a) => (
          <div
            key={a.id}
            style={{
              borderLeft: "3px solid var(--border)",
              paddingLeft: 12,
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                marginBottom: 4,
              }}
            >
              <span className={`badge ${severityClass[a.severity]}`}>
                {a.severity}
              </span>
              <strong style={{ fontSize: 13 }}>{a.name}</strong>
            </div>
            <div style={{ color: "var(--text-muted)", fontSize: 12 }}>
              {a.message}
            </div>
            <div style={{ color: "var(--text-dim)", fontSize: 11, marginTop: 4 }}>
              {a.source ?? "system"} ·{" "}
              {new Date(a.triggered_at).toLocaleString()}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
