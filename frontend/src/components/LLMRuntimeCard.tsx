import React from "react";
import type { LLMRuntimeReport } from "../services/api";

const formatBytes = (n: number): string => {
  if (n <= 0) return "—";
  const units = ["B", "KB", "MB", "GB", "TB"];
  let i = 0;
  let v = n;
  while (v >= 1024 && i < units.length - 1) {
    v /= 1024;
    i++;
  }
  return `${v.toFixed(1)} ${units[i]}`;
};

interface Props {
  report: LLMRuntimeReport;
}

export const LLMRuntimeCard: React.FC<Props> = ({ report }) => {
  const { status, models } = report;
  return (
    <div className="card">
      <p className="card-title">LLM Runtime — {status.provider}</p>
      <div style={{ display: "flex", gap: 16, alignItems: "center", marginBottom: 16 }}>
        <span className={`badge ${status.reachable ? "success" : "danger"}`}>
          {status.reachable ? "online" : "offline"}
        </span>
        <span style={{ color: "var(--text-muted)", fontSize: 12 }}>{status.base_url}</span>
        {status.latency_ms != null && (
          <span style={{ color: "var(--text-muted)", fontSize: 12 }}>
            {status.latency_ms.toFixed(0)} ms
          </span>
        )}
      </div>
      {status.error && <div className="error-box" style={{ marginBottom: 12 }}>{status.error}</div>}
      {models.length === 0 ? (
        <p style={{ color: "var(--text-muted)", fontSize: 13, margin: 0 }}>
          No models reported. Pull a model with{" "}
          <code style={{ color: "var(--accent)" }}>ollama pull llama3</code>.
        </p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Model</th>
              <th>Params</th>
              <th>Quant</th>
              <th>Size</th>
            </tr>
          </thead>
          <tbody>
            {models.map((m) => (
              <tr key={m.name}>
                <td style={{ fontWeight: 500 }}>{m.name}</td>
                <td>{m.parameter_size ?? "—"}</td>
                <td>{m.quantization ?? "—"}</td>
                <td>{formatBytes(m.size_bytes)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};
