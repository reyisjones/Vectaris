/**
 * Toast container — renders active toasts from ToastContext and polls for
 * critical alerts to surface them as notifications.
 */
import { useQuery } from "@tanstack/react-query";
import React, { useEffect, useRef } from "react";
import { getAlerts } from "../services/api";
import { useToast } from "./ToastContext";

const SEVERITY_COLOR: Record<string, string> = {
  critical: "var(--danger, #ef4444)",
  high: "var(--warn, #f59e0b)",
  medium: "var(--accent, #7c3aed)",
  low: "var(--text-muted, #8b8fa8)",
};

export const ToastContainer: React.FC = () => {
  const { toasts, removeToast, addToast } = useToast();
  const seenIds = useRef<Set<string>>(new Set());

  // Poll for critical alerts and surface new ones as toasts.
  const { data: alerts } = useQuery({
    queryKey: ["alerts-toast"],
    queryFn: getAlerts,
    refetchInterval: 15_000,
  });

  useEffect(() => {
    if (!alerts) return;
    for (const alert of alerts) {
      if (
        (alert.severity === "critical" || alert.severity === "high") &&
        !alert.resolved &&
        !seenIds.current.has(alert.id)
      ) {
        seenIds.current.add(alert.id);
        addToast(alert.message, alert.severity);
      }
    }
  }, [alerts, addToast]);

  if (toasts.length === 0) return null;

  return (
    <div
      style={{
        position: "fixed",
        bottom: "1.5rem",
        right: "1.5rem",
        display: "flex",
        flexDirection: "column",
        gap: "0.5rem",
        zIndex: 9999,
        maxWidth: "360px",
      }}
    >
      {toasts.map((t) => (
        <div
          key={t.id}
          style={{
            background: "var(--surface-2, #1e1e2e)",
            borderLeft: `4px solid ${SEVERITY_COLOR[t.severity] ?? SEVERITY_COLOR.medium}`,
            borderRadius: "0.5rem",
            padding: "0.6rem 0.85rem",
            boxShadow: "0 4px 16px rgba(0,0,0,0.4)",
            display: "flex",
            alignItems: "flex-start",
            gap: "0.6rem",
            animation: "slideIn 0.2s ease-out",
          }}
        >
          <span
            style={{
              fontSize: "0.7rem",
              fontWeight: 700,
              textTransform: "uppercase",
              color: SEVERITY_COLOR[t.severity],
              whiteSpace: "nowrap",
              paddingTop: "1px",
            }}
          >
            {t.severity}
          </span>
          <span style={{ fontSize: "0.82rem", flex: 1, lineHeight: 1.4 }}>
            {t.message}
          </span>
          <button
            onClick={() => removeToast(t.id)}
            style={{
              background: "none",
              border: "none",
              cursor: "pointer",
              color: "var(--text-muted)",
              fontSize: "1rem",
              lineHeight: 1,
              padding: 0,
            }}
            aria-label="Dismiss"
          >
            ×
          </button>
        </div>
      ))}
      <style>{`
        @keyframes slideIn {
          from { transform: translateX(110%); opacity: 0; }
          to   { transform: translateX(0);    opacity: 1; }
        }
      `}</style>
    </div>
  );
};
