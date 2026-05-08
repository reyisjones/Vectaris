import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { AgentHealthTable } from "../../components/AgentHealthTable";
import type { Agent } from "../../services/api";

const makeAgent = (overrides: Partial<Agent> = {}): Agent => ({
  id: "agent-1",
  name: "test-agent",
  model: "gpt-4o",
  status: "healthy",
  uptime_seconds: 3600,
  task_success_rate: 0.98,
  tasks_per_minute: 12,
  last_seen: new Date().toISOString(),
  ...overrides,
});

describe("AgentHealthTable", () => {
  it("renders table headers", () => {
    render(<AgentHealthTable agents={[]} />);
    expect(screen.getByText("Name")).toBeInTheDocument();
    expect(screen.getByText("Model")).toBeInTheDocument();
    expect(screen.getByText("Status")).toBeInTheDocument();
    expect(screen.getByText("Uptime")).toBeInTheDocument();
    expect(screen.getByText("Success Rate")).toBeInTheDocument();
    expect(screen.getByText("Tasks/min")).toBeInTheDocument();
  });

  it("renders an empty table without crashing", () => {
    render(<AgentHealthTable agents={[]} />);
    expect(screen.queryAllByRole("row")).toHaveLength(1); // header row only
  });

  it("renders one agent row with correct data", () => {
    render(<AgentHealthTable agents={[makeAgent()]} />);
    expect(screen.getByText("test-agent")).toBeInTheDocument();
    expect(screen.getByText("gpt-4o")).toBeInTheDocument();
    expect(screen.getByText("healthy")).toBeInTheDocument();
    expect(screen.getByText("1h")).toBeInTheDocument(); // 3600s → 1h
    expect(screen.getByText("98.0%")).toBeInTheDocument();
    expect(screen.getByText("12")).toBeInTheDocument();
  });

  it("renders multiple agents", () => {
    const agents = [
      makeAgent({ id: "1", name: "agent-a" }),
      makeAgent({ id: "2", name: "agent-b", status: "degraded" }),
    ];
    render(<AgentHealthTable agents={agents} />);
    expect(screen.getByText("agent-a")).toBeInTheDocument();
    expect(screen.getByText("agent-b")).toBeInTheDocument();
    expect(screen.getByText("degraded")).toBeInTheDocument();
  });

  it("formats uptime in minutes for < 1h", () => {
    render(<AgentHealthTable agents={[makeAgent({ uptime_seconds: 1800 })]} />);
    expect(screen.getByText("30m")).toBeInTheDocument();
  });

  it("formats uptime in days for >= 24h", () => {
    render(<AgentHealthTable agents={[makeAgent({ uptime_seconds: 172800 })]} />);
    expect(screen.getByText("2d")).toBeInTheDocument();
  });

  it("shows unhealthy badge with correct text", () => {
    render(<AgentHealthTable agents={[makeAgent({ status: "unhealthy" })]} />);
    expect(screen.getByText("unhealthy")).toBeInTheDocument();
  });
});
