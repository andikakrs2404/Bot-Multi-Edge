# ADR-011: Feedback Domain

- **Layer:** 1 (Research) + 2 (Production) bridge
- **Status:** Draft (NOT RATIFIED)
- **Date:** 2026-08-01
- **Depends On:** ADR-002 (Ontology), ADR-002A (Lifecycles), ADR-010 (Execution)
- **Supersedes:** nothing

## Context

AlphaOS's core invariant is: **"Knowledge Evolves; It Is Never
Overwritten."** Today the pipeline ends at the ProductionLedger:

```text
Knowledge → Signal → Decision → Ledger → Replay
```

There is no loop back. An Edge that was validated on historical data
can drift in live production, and nothing observes that. Feedback is
the mechanism that closes the loop: outcomes of Production Decisions
become new Evidence, which re-validates or decays Edges (ADR-002A).

## Decision

### Aggregate Roots

| Entity | Kind | Nature |
|--------|------|--------|
| `Outcome` | Aggregate Root | Measured result of a ProductionDecision over a window: realized PnL, hit/miss vs. forecast direction, slippage. Immutable. |
| `DriftObservation` | Entity | A measured deviation of live feature/edge behavior from validation-time distribution. Feeds decay logic. |

### Loop

```text
ProductionDecision
    → Outcome (measured after window closes)
    → Feedback (structured observation)
    → Evidence (new, appended — never overwrites)
    → Revalidation / EdgeDecay (ADR-002A lifecycle)
```

Key property: feedback NEVER mutates existing Evidence or Edge. It
appends new Evidence; the lifecycle engine decides whether the Edge
stays ACTIVE, becomes DECAYED, or is re-validated.

### Boundaries

Feedback Domain:

- MAY read: ProductionDecision, Edge, Evidence (append-only writes)
- MAY write: new Evidence (via research protocol, ADR-008)
- MUST NOT: mutate existing Edge/Evidence; MUST NOT touch Order/Position
  internals (ADR-010)

### Invariants

1. Outcome is immutable and content-addressed (ADR-001).
2. Outcome links to exactly one decision_id (from ProductionLedger).
3. Feedback produces NEW Evidence; never UPDATE/DELETE.
4. EdgeDecay only via ActivationEngine lifecycle (ADR-002A):
   ACTIVE→DECAYED requires stale evidence, never direct feedback write.

## Consequences

Positive:

- Knowledge evolution becomes observable and auditable.
- Drift detection is a first-class citizen, not a hack.
- Revalidation uses the same ValidatorEngine as research — one path.

Negative:

- Outcome windows require position/execution data (ADR-010) — Feedback
  depends on Execution for realized PnL.
- Live data ingestion adds operational surface.

Neutral:

- Research replay (ADR-007 reproducibility) is unaffected; feedback is
  append-only and never rewrites history.

## Alternatives Considered

1. Skip feedback; decay edges by staleness only — rejected: misses
  live drift, the main failure mode of validated edges.
2. Feedback writes directly to Edge status — rejected: violates
  "never overwritten"; lifecycle is governed by ADR-002A.
3. Fold feedback into ADR-010 — rejected: execution is mechanical,
  feedback is epistemological; separate concerns.
