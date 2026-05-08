import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { MetricCard } from "../../components/MetricCard";

describe("MetricCard", () => {
  it("renders title and value", () => {
    render(<MetricCard title="Total Requests" value={1234} />);
    expect(screen.getByText("Total Requests")).toBeInTheDocument();
    expect(screen.getByText(1234)).toBeInTheDocument();
  });

  it("renders subtitle when provided", () => {
    render(<MetricCard title="Cost" value="$42.00" subtitle="last 30d" />);
    expect(screen.getByText("last 30d")).toBeInTheDocument();
  });

  it("does not render subtitle when omitted", () => {
    render(<MetricCard title="Cost" value="$42.00" />);
    expect(screen.queryByText("last 30d")).not.toBeInTheDocument();
  });

  it("renders trend arrow and value for up trend", () => {
    render(
      <MetricCard
        title="Requests"
        value={500}
        trend="up"
        trendValue="+12% vs prior period"
      />,
    );
    expect(screen.getByText(/\+12% vs prior period/)).toBeInTheDocument();
    expect(screen.getByText(/↑/)).toBeInTheDocument();
  });

  it("renders down arrow for down trend", () => {
    render(
      <MetricCard title="Errors" value="5%" trend="down" trendValue="-3% MoM" />,
    );
    expect(screen.getByText(/↓/)).toBeInTheDocument();
  });

  it("does not render trend row when trendValue is absent", () => {
    render(<MetricCard title="Latency" value="320ms" trend="up" />);
    // trend arrow row is not rendered
    expect(screen.queryByText(/↑/)).not.toBeInTheDocument();
  });

  it("accepts string values", () => {
    render(<MetricCard title="Error Rate" value="0.12%" />);
    expect(screen.getByText("0.12%")).toBeInTheDocument();
  });
});
