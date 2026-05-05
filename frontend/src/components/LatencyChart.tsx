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

interface Props {
  data: LatencyMetric[];
}

export const LatencyChart: React.FC<Props> = ({ data }) => (
  <div className="card">
    <p className="card-title">Latency by Model (ms)</p>
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data} barCategoryGap="20%">
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
        <XAxis dataKey="model" stroke="#64748b" tick={{ fontSize: 11 }} />
        <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
        <Tooltip
          contentStyle={{
            background: "#0f172a",
            border: "1px solid #334155",
            borderRadius: 6,
            fontSize: 12,
          }}
        />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Bar dataKey="p50_ms" name="P50" fill="#38bdf8" radius={[4, 4, 0, 0]} />
        <Bar dataKey="p95_ms" name="P95" fill="#f59e0b" radius={[4, 4, 0, 0]} />
        <Bar dataKey="p99_ms" name="P99" fill="#ef4444" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  </div>
);
