import React from "react";

interface Props {
  rows?: number;
}

export const LoadingCard: React.FC<Props> = ({ rows = 3 }) => (
  <div className="card">
    <div className="skeleton" style={{ width: "40%", marginBottom: 12 }} />
    {Array.from({ length: rows }).map((_, i) => (
      <div
        key={i}
        className="skeleton"
        style={{ marginBottom: 8, width: `${80 - i * 10}%` }}
      />
    ))}
  </div>
);

export const ErrorCard: React.FC<{ message: string }> = ({ message }) => (
  <div className="error-box">⚠ {message}</div>
);
