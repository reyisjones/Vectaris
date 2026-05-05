/**
 * Recharts tooltip styling derived from theme tokens defined in
 * `src/styles/global.css`. Recharts requires inline styles so we
 * hydrate from CSS variables at runtime to keep a single source of truth.
 */

const cssVar = (name: string, fallback: string): string => {
  if (typeof window === "undefined") return fallback;
  const value = getComputedStyle(document.documentElement)
    .getPropertyValue(name)
    .trim();
  return value || fallback;
};

export const tooltipStyle = (): React.CSSProperties => ({
  background: cssVar("--bg-elev", "#111827"),
  border: `1px solid ${cssVar("--border", "#334155")}`,
  borderRadius: 6,
  fontSize: 12,
  color: cssVar("--text", "#f1f5f9"),
});

export const axisStroke = (): string => cssVar("--text-dim", "#64748b");
export const gridStroke = (): string => cssVar("--border", "#334155");
