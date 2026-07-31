# ADR-001: Engineering Principles

- **Layer:** 0 (Constitution)
- **Status:** Draft
- **Date:** 2026-07-29
- **Depends On:** ADR-000B

## Context

The Vision (ADR-000) defines WHAT AlphaOS is. This ADR fixes HOW its components are engineered — the non-negotiable principles every module, engine, and script must obey. These principles exist to make the system deterministic, reproducible, and auditable at scale.

## Decision

1. **Contract-First.** Every interface between components is defined by a versioned contract (schema, protocol) BEFORE implementation. Code that implements a contract may change; contracts change only via ADR.
2. **Immutability by Default.** No artifact is edited in place. Change produces a new versioned artifact. This is the bedrock of reproducibility.
3. **Stateless Engines, Stateful AKB.** Engines hold no long-lived state; all persistent state lives in the AKB. Engines read input artifacts, transform, emit output artifacts.
4. **Artifact-Driven Flow.** The pipeline progresses by producing and consuming versioned artifacts, not by ephemeral events. An engine activates when its declared input artifacts are present and version-consistent.
5. **Reproducibility is a Requirement.** Every output can be regenerated from: dataset version, registry versions, rule version, experiment config, git commit, random seed, and constitution hash.
6. **Deterministic Production.** Research may be stochastic. Production must be deterministic: same AKB state + same market input ⇒ same decision.
7. **Enforced Dependency Direction.** `production → shared contracts ← research`. The two realms never import each other's code.
8. **Explainability Before Performance.** Every Edge promoted to Knowledge must be explainable in domain terms. Black-box models may be used during discovery but never as final production edges.
9. **Auditability is Non-Negotiable.** Every ProductionDecision is traceable: decision → edges → evidence → experiment → dataset → git commit.

## Consequences

- **Positive:** Deterministic, auditable, and maintainable system; safe parallel development of research and production.
- **Negative:** More upfront contract design; some convenience sacrificed. Accepted.

## Alternatives Considered

- **Event-driven everything:** Rejected — replay and reproducibility are harder with ephemeral events.
- **Shared mutable state:** Rejected — violates determinism and auditability.

## Migration Path

None for v1.0.
