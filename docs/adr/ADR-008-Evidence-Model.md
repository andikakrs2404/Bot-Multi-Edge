# ADR-008: Evidence Model

- **Layer:** 1 (Domain & Contracts)
- **Status:** Ratified
- **Date:** 2026-07-29
- **Depends On:** ADR-007

## Context

Evidence is what separates Knowledge from opinion. To be auditable, evidence must be complete, immutable, and structurally uniform. This ADR fixes what constitutes Evidence and how it is recorded and attached to Edges.

## Decision

### Evidence Definition

**Evidence** = the complete, immutable set of statistical outputs produced by an Experiment for a Candidate, plus the configuration that produced them.

### Evidence Components

For each Candidate, an `EvidenceBundle` (contract per ADR-003) contains:

1. **Performance metrics** — per fold and aggregate: return statistics, win rate, profit factor, expectancy, Sharpe/Sortino, max drawdown, turnover, capacity estimate.
2. **Validation reports** — walk-forward report, OOS report, stability report (regime × segment breakdown), sensitivity analysis.
3. **Anti-overfitting results** — multiple-testing p-values / reality check, bootstrap CIs, Monte Carlo equity distribution, probability of ruin.
4. **Trade log reference** — pointer to the simulated trades artifact (hash), never inlined.
5. **Provenance** — ExperimentID, DatasetIDs, registry versions, constitution_hash, git commit, seeds.

### Immutability & Attachment

- EvidenceBundles are write-once artifacts (Axiom 1, ADR-002).
- An Edge is `supported_by` exactly the EvidenceBundle of the Experiment that produced it.
- Evidence can refute a Candidate (then it never becomes an Edge) — refuting evidence is still recorded in the AKB.

### Metric Definitions

Canonical metric formulas are defined in `docs/specifications/` so every module computes them identically (no duplicated, drifting definitions).

## Consequences

- **Positive:** Complete audit trail; uniform metrics; refutation is preserved as knowledge; strong anti-fraud properties.
- **Negative:** Evidence storage grows. Accepted — it is the product of the system.

## Alternatives Considered

- **Summary-only evidence (single metrics row):** Rejected — loses auditability and trade-level analysis.
- **Evidence inside edge records:** Rejected — blurs Knowledge/Evidence separation (ADR-002).

## Migration Path

None for v1.0.
