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
import { axisStroke, gridStroke, tooltipStyle } from "./chartTheme";

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
        <CartesianGrid strokeDasharray="3 3" stroke={gridStroke()} />
        <XAxis dataKey={dimension} stroke={axisStroke()} tick={{ fontSize: 11 }} />
        <YAxis stroke={axisStroke()} tick={{ fontSize: 11 }} />
        <Tooltip
          contentStyle={tooltipStyle()}
          formatter={(v: number) => `$${v.toFixed(2)}`}
        />
        <Bar dataKey="usd_cost" fill="var(--accent-2)" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  </div>
);
