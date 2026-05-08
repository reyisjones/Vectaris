# ADR-002: Use Prometheus + PromQL as the Primary Metrics Source

**Status:** Accepted  
**Date:** 2025-01-20  
**Deciders:** Vectaris core team

---

## Context

The platform must surface real-time latency percentiles, request rates, and error
rates for AI agents running in production. Multiple options exist for storing and
querying this time-series data.

Requirements:
- Sub-second query latency for dashboard refresh
- Native histogram support for p50/p95/p99 calculations
- Easy instrumentation of Python/Node services via client libraries
- Self-hostable with no per-seat licensing
- Kubernetes-native operator for automated scraping

Candidates evaluated: **Prometheus**, Datadog, Grafana Mimir, InfluxDB, Azure Monitor.

## Decision

Use **Prometheus** as the primary time-series store with **PromQL** for queries.
Expose metrics from the FastAPI backend via the `prometheus-fastapi-instrumentator`
auto-instrumentation library. Provide a Grafana dashboard JSON for visualization.

## Consequences

**Positive:**
- `prometheus-fastapi-instrumentator` zero-config instruments all routes with
  `http_request_duration_seconds` histograms — p50/p95/p99 derived via
  `histogram_quantile()`.
- `ServiceMonitor` CRD integrates with Prometheus Operator for automatic scraping
  — no manual job configuration.
- Grafana dashboard JSON is version-controlled and applied via provisioning.
- Stub fallback (deterministic demo data) activates when `PROMETHEUS_URL` is unset,
  enabling development without a running Prometheus instance.

**Negative / trade-offs:**
- Prometheus stores raw time-series; long-term retention requires Thanos or Cortex.
  Acceptable for the initial release.
- PromQL has a learning curve compared to SQL-based query languages.
- No managed cloud offering without a third-party service like Grafana Cloud.

## Alternatives Considered

| Option | Rejected because |
|--------|-----------------|
| Datadog | Per-host pricing; vendor lock-in |
| Azure Monitor | Only viable on Azure; no local dev story |
| InfluxDB | InfluxQL less widely known; Prometheus is standard for K8s |
| Grafana Mimir | Adds operational complexity; Prometheus sufficient at this scale |
