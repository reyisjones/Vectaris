import React from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { LatencyMetric } from "../services/api";
import { axisStroke, gridStroke, tooltipStyle } from "./chartTheme";

interface Props {
  data: LatencyMetric[];
}

export const LatencyChart: React.FC<Props> = ({ data }) => (
  <div className="card">
    <p className="card-title">Latency by Model (ms)</p>
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data} barCategoryGap="20%">
        <CartesianGrid strokeDasharray="3 3" stroke={gridStroke()} />
        <XAxis dataKey="model" stroke={axisStroke()} tick={{ fontSize: 11 }} />
        <YAxis stroke={axisStroke()} tick={{ fontSize: 11 }} />
        <Tooltip contentStyle={tooltipStyle()} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Bar dataKey="p50_ms" name="P50" fill="var(--accent)" radius={[4, 4, 0, 0]} />
        <Bar dataKey="p95_ms" name="P95" fill="var(--warn)" radius={[4, 4, 0, 0]} />
        <Bar dataKey="p99_ms" name="P99" fill="var(--danger)" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  </div>
);
