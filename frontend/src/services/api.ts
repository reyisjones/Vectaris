import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 10_000,
  headers: { "Content-Type": "application/json" },
});

// --- Types ---
export interface UsageMetric {
  timestamp: string;
  model: string;
  total_requests: number;
  total_tokens: number;
  error_count: number;
  error_rate: number;
}

export interface UsageSummary {
  total_requests: number;
  total_tokens: number;
  error_rate: number;
  models: UsageMetric[];
}

export interface LatencyMetric {
  timestamp: string;
  model: string;
  p50_ms: number;
  p95_ms: number;
  p99_ms: number;
}

export interface LatencySummary {
  models: LatencyMetric[];
}

export type AgentStatus = "healthy" | "degraded" | "unhealthy" | "unknown";

export interface Agent {
  id: string;
  name: string;
  model: string;
  status: AgentStatus;
  uptime_seconds: number;
  task_success_rate: number;
  tasks_per_minute: number;
  last_seen: string;
}

export interface AgentHealth {
  agent_id: string;
  status: AgentStatus;
  latency_ms: number;
  error_rate: number;
  checked_at: string;
}

export interface CostRecord {
  model: string;
  team: string;
  usd_cost: number;
  token_count: number;
  request_count: number;
}

export interface CostSummary {
  total_usd: number;
  period: string;
  by_model: CostRecord[];
  by_team: CostRecord[];
}

export interface CostForecast {
  horizon_days: number;
  projected_usd: number;
  daily_run_rate_usd: number;
  generated_at: string;
}

export type AlertSeverity = "critical" | "high" | "medium" | "low";

export interface Alert {
  id: string;
  name: string;
  severity: AlertSeverity;
  message: string;
  triggered_at: string;
  resolved: boolean;
  source?: string;
}

export interface LLMRuntimeStatus {
  provider: string;
  base_url: string;
  reachable: boolean;
  latency_ms: number | null;
  error: string | null;
  checked_at: string;
}

export interface LLMModelInfo {
  name: string;
  size_bytes: number;
  parameter_size: string | null;
  quantization: string | null;
  modified_at: string | null;
}

export interface LLMRuntimeReport {
  status: LLMRuntimeStatus;
  models: LLMModelInfo[];
}

// --- API calls ---
export const getUsageMetrics = () =>
  api.get<UsageSummary>("/api/v1/metrics/usage").then((r) => r.data);

export const getLatencyMetrics = () =>
  api.get<LatencySummary>("/api/v1/metrics/latency").then((r) => r.data);

export const getAgents = () =>
  api.get<Agent[]>("/api/v1/agents").then((r) => r.data);

export const getAgentHealth = (id: string) =>
  api.get<AgentHealth>(`/api/v1/agents/${id}/health`).then((r) => r.data);

export const getCosts = (period = "30d") =>
  api.get<CostSummary>("/api/v1/costs", { params: { period } }).then((r) => r.data);

export const getCostForecast = (horizonDays = 30) =>
  api
    .get<CostForecast>("/api/v1/costs/forecast", {
      params: { horizon_days: horizonDays },
    })
    .then((r) => r.data);

export const getAlerts = () =>
  api.get<Alert[]>("/api/v1/alerts").then((r) => r.data);

export const getLLMRuntime = () =>
  api.get<LLMRuntimeReport>("/api/v1/llm/runtime").then((r) => r.data);
