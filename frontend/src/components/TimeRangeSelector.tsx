import React from "react";

export type TimePeriod = "1h" | "24h" | "7d" | "30d";

const OPTIONS: { value: TimePeriod; label: string }[] = [
  { value: "1h", label: "1h" },
  { value: "24h", label: "24h" },
  { value: "7d", label: "7d" },
  { value: "30d", label: "30d" },
];

interface Props {
  value: TimePeriod;
  onChange: (period: TimePeriod) => void;
}

export const TimeRangeSelector: React.FC<Props> = ({ value, onChange }) => (
  <div
    style={{
      display: "inline-flex",
      gap: "0.25rem",
      background: "var(--surface-2, #1e1e2e)",
      borderRadius: "0.5rem",
      padding: "0.2rem",
    }}
  >
    {OPTIONS.map((opt) => (
      <button
        key={opt.value}
        onClick={() => onChange(opt.value)}
        style={{
          padding: "0.25rem 0.7rem",
          borderRadius: "0.35rem",
          border: "none",
          cursor: "pointer",
          fontWeight: value === opt.value ? 600 : 400,
          background:
            value === opt.value
              ? "var(--accent, #7c3aed)"
              : "transparent",
          color:
            value === opt.value
              ? "#fff"
              : "var(--text-muted, #8b8fa8)",
          fontSize: "0.8rem",
          transition: "background 0.15s, color 0.15s",
        }}
      >
        {opt.label}
      </button>
    ))}
  </div>
);
