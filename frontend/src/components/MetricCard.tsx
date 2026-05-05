import React from "react";

interface Props {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: "up" | "down" | "neutral";
  trendValue?: string;
}

const trendColor = {
  up: "var(--success)",
  down: "var(--danger)",
  neutral: "var(--text-muted)",
} as const;

const trendArrow = { up: "↑", down: "↓", neutral: "→" } as const;

export const MetricCard: React.FC<Props> = ({
  title,
  value,
  subtitle,
  trend = "neutral",
  trendValue,
}) => (
  <div className="card" style={{ minWidth: 180 }}>
    <p className="card-title">{title}</p>
    <p style={{ color: "var(--text)", fontSize: 28, fontWeight: 700, margin: "0.25rem 0" }}>
      {value}
    </p>
    {subtitle && (
      <p style={{ color: "var(--text-dim)", fontSize: 11, margin: 0 }}>{subtitle}</p>
    )}
    {trendValue && (
      <p style={{ color: trendColor[trend], fontSize: 12, margin: "0.4rem 0 0" }}>
        {trendArrow[trend]} {trendValue}
      </p>
    )}
  </div>
);
