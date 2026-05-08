import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { LatencyChart } from "../../components/LatencyChart";
import type { LatencyMetric } from "../../services/api";

// Recharts uses ResizeObserver which is not available in jsdom
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));

const makeMetric = (model: string, p50: number, p95: number, p99: number): LatencyMetric => ({
  timestamp: new Date().toISOString(),
  model,
  p50_ms: p50,
  p95_ms: p95,
  p99_ms: p99,
});

describe("LatencyChart", () => {
  it("renders card title", () => {
    render(<LatencyChart data={[]} />);
    expect(screen.getByText("Latency by Model (ms)")).toBeInTheDocument();
  });

  it("renders with multiple model data points", () => {
    const data = [
      makeMetric("gpt-4o", 320, 850, 1200),
      makeMetric("gpt-4o-mini", 180, 420, 680),
    ];
    render(<LatencyChart data={data} />);
    // Card title present, Recharts renders SVG — no crashes
    expect(screen.getByText("Latency by Model (ms)")).toBeInTheDocument();
  });

  it("renders without crashing on empty data", () => {
    expect(() => render(<LatencyChart data={[]} />)).not.toThrow();
  });
});
