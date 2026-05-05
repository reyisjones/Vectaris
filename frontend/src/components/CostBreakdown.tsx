import React from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { CostRecord } from "../services/api";

interface Props {
  title: string;
  records: CostRecord[];
  dimension: "model" | "team";
}

export const CostBreakdown: React.FC<Props> = ({ title, records, dimension }) => (
  <div className="card">
    <p className="card-title">{title}</p>
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={records}>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
        <XAxis dataKey={dimension} stroke="#64748b" tick={{ fontSize: 11 }} />
        <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
        <Tooltip
          contentStyle={{
            background: "#0f172a",
            border: "1px solid #334155",
            borderRadius: 6,
            fontSize: 12,
          }}
          formatter={(v: number) => `$${v.toFixed(2)}`}
        />
        <Bar dataKey="usd_cost" fill="#818cf8" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  </div>
);
