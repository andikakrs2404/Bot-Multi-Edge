# ADR-010: Execution Domain

- **Layer:** 2 (Production & Execution)
- **Status:** Draft (NOT RATIFIED)
- **Date:** 2026-08-01
- **Depends On:** ADR-002 (Ontology), ADR-000B (Trust Model)
- **Supersedes:** nothing

## Context

AlphaOS Core v1.0 (ADR-000..009) is complete: Research → Knowledge →
Production → Audit. The Production Domain ends at ProductionDecision,
persisted in the ProductionLedger. There is no path to a live exchange.

Execution is a NEW domain with its own ontology. It is NOT part of
ADR-002. Ratifying this ADR extends the constitution with Layer 2
entities; until ratified, no execution code may be written.

## Decision

### Aggregate Roots

| Entity | Kind | Nature |
|--------|------|--------|
| `OrderIntent` | Aggregate Root | Immutable expression of what Production wants to do. Born from exactly one ProductionDecision. |
| `Order` | Aggregate Root | A concrete order submitted to an exchange. Born from exactly one OrderIntent. |
| `ExecutionReport` | Aggregate Root | Exchange's response to an Order: fill, partial fill, reject. Born from exactly one Order. |
| `Position` | Aggregate Root | Derived state over ExecutionReports. Never written directly; computed. |

### Boundaries

Execution Domain:

- MAY read: ProductionDecision, Portfolio, Symbol
- MUST NOT read: Experiment, Evidence, Dataset, Feature, Candidate, Label

This keeps the Research ↔ Production boundary clean (ADR-000B):
execution consumes only the auditable decision artifact, never research
internals.

### Invariants

1. OrderIntent immutable (content-addressed, ADR-001).
2. Order born from one OrderIntent; order_id links intent_id.
3. ExecutionReport born from one Order; report_id links order_id.
4. Position is derived from ExecutionReports — never a write target.
5. Every OrderIntent traces to a decision_id in the ProductionLedger
   (audit: no orphan intents).

### Epistemological Placement

```text
... → ProductionDecision → OrderIntent → Order → ExecutionReport → Position
```

Production → Execution is a strict downward flow. Feedback (outcome →
evidence) is a SEPARATE domain (ADR-011) and does not flow through
execution internals.

## Consequences

Positive:

- Execution is isolatable and testable with a fake exchange.
- Audit trail: decision → intent → order → report → position.
- No research leakage into execution path.

Negative:

- More moving parts; broker adapters are I/O-heavy.
- Position derivation must handle partial fills, cancels, rejects.

Neutral:

- Exchange specifics (venue, API, order types) live behind an adapter
  interface, not in the ontology.

## Alternatives Considered

1. Extend ProductionDecision with order fields — rejected: mixes
   decision purity with execution mechanics.
2. Execution as part of ADR-002 — rejected: ADR-002 is frozen v1.0;
   new domain deserves its own ratification.
3. No Execution domain (paper-only) — viable for research, but AlphaOS
   production mandate requires the boundary to exist now.
