# ADR-003: Use React + Vite for the Frontend

**Status:** Accepted  
**Date:** 2025-01-22  
**Deciders:** Vectaris core team

---

## Context

We needed a frontend framework for the observability dashboard. Key requirements:

- Fast development iteration (HMR)
- TypeScript-first
- Strong ecosystem for data-fetching, charting, and routing
- No server-side rendering required (dashboard is behind auth)
- Lightweight build output for container deployment

Candidates evaluated: **React + Vite**, Next.js, Vue 3 + Vite, Svelte.

## Decision

Use **React 18** with **Vite** as the build tool. Supporting libraries:

| Concern | Library |
|---------|---------|
| Data fetching / caching | TanStack Query v5 |
| Client-side routing | React Router v6 |
| Charts | Recharts |
| HTTP client | Axios |
| Real-time metrics | Browser `EventSource` (SSE) |
| Observability | OTel Browser SDK + web-vitals |

## Consequences

**Positive:**
- Vite HMR is ~10× faster than webpack-based CRA for large component trees.
- TanStack Query handles cache invalidation, background refetch, and stale-while-
  revalidate out of the box — no custom polling logic in components.
- React 18 concurrent features (Suspense, transitions) available for future use.
- Recharts renders SVG with minimal config; theming via CSS variables.
- OTel Browser SDK enables distributed tracing from the browser to the backend
  (trace context propagated via `traceparent` header on Axios requests).

**Negative / trade-offs:**
- No SSR means the first paint requires JS execution; acceptable for an internal
  dashboard.
- Bundle size is larger than a Svelte or vanilla JS app. Mitigated by code-splitting
  at the route level and Vite's tree-shaking.
- React requires explicit memoization (`useMemo`, `useCallback`) for performance-
  critical paths.

## Alternatives Considered

| Option | Rejected because |
|--------|-----------------|
| Next.js | SSR/SSG complexity not needed; slower HMR in dev |
| Vue 3 + Vite | Smaller ecosystem for observability/dashboard libraries |
| Svelte | Smaller team familiarity; fewer TypeScript examples |
| Plain HTML + Vanilla JS | No component reuse; harder to maintain at scale |
