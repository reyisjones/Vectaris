# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for the Vectaris project.
ADRs document important technical decisions, the context in which they were made,
and the consequences of choosing one approach over alternatives.

## Format

Each ADR is a Markdown file named `NNN-short-title.md` where `NNN` is a zero-padded
sequential number. Status values: **Proposed** · **Accepted** · **Deprecated** · **Superseded**.

## Index

| # | Title | Status |
|---|-------|--------|
| [001](001-use-fastapi-for-backend.md) | Use FastAPI for the observability backend | Accepted |
| [002](002-prometheus-as-metrics-source.md) | Use Prometheus + PromQL as the primary metrics source | Accepted |
| [003](003-react-vite-frontend.md) | Use React + Vite for the frontend | Accepted |
| [004](004-hierarchical-authentication.md) | Hierarchical authentication: OIDC → API key → open | Accepted |
| [005](005-sse-over-websocket.md) | Use Server-Sent Events instead of WebSockets for live metrics | Accepted |
| [006](006-helm-for-kubernetes-packaging.md) | Use Helm for Kubernetes packaging | Accepted |
