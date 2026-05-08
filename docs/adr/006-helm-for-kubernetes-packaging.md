# ADR-006: Use Helm for Kubernetes Packaging

**Status:** Accepted  
**Date:** 2025-04-20  
**Deciders:** Vectaris core team

---

## Context

The platform has multiple Kubernetes resources (Deployments, Services, Ingress,
HPA, ServiceMonitor, Secrets, ConfigMaps, ServiceAccount). Managing these as
plain YAML manifests requires manual variable substitution and makes it hard to
deploy to multiple environments (dev, staging, production) with different
configurations.

Options evaluated: **Helm**, Kustomize, plain YAML, Timoni (CUE-based).

## Decision

Package all Kubernetes resources as a **Helm chart** at `deploy/helm/vectaris/`
(version `1.0.0`).

## Consequences

**Positive:**
- Single `values.yaml` overrides environment-specific settings without duplicating
  manifests.
- Optional components (HPA, ServiceMonitor, TLS) are toggled with boolean flags
  — no separate overlay directories.
- `helm upgrade --install` provides idempotent, atomic deployments with rollback
  support (`helm rollback`).
- `NOTES.txt` prints actionable post-install instructions.
- Helm's `checksum/config` annotation on Deployments triggers pod restarts when
  ConfigMaps change — no manual rollout restart needed.
- The chart is self-contained and can be published to a Helm repository (OCI or
  classic) for GitOps (ArgoCD, Flux) adoption.

**Negative / trade-offs:**
- Helm templates (Go templating) are harder to read than plain YAML.
- Helm v3 stores release state in cluster Secrets — accidental deletion of the
  namespace can lose release history.
- Complex conditional logic in templates is difficult to unit-test; `helm lint`
  and `helm template` provide basic validation only.

## Alternatives Considered

| Option | Rejected because |
|--------|-----------------|
| Kustomize | No templating (patches only); harder multi-env config |
| Plain YAML | Manual `envsubst`; no rollback; no packaging |
| Timoni / CUE | Immature ecosystem; unfamiliar to most operators |
