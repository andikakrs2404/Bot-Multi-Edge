# ADR-007: Experiment Protocol

- **Layer:** 1 (Domain & Contracts)
- **Status:** Draft
- **Date:** 2026-07-29
- **Depends On:** ADR-006

## Context

An Experiment is the atomic unit of research. For results to be comparable and reproducible, every Experiment must follow one protocol: declare everything up front, execute deterministically, validate rigorously, and record all provenance. This ADR fixes that protocol.

## Decision

### ExperimentConfig (declared BEFORE execution)

Every Experiment declares, in `ExperimentConfig` (contract per ADR-003):
- `ExperimentID` (assigned at DRAFT),
- `constitution_hash` (ADR-001A),
- `dataset_ids` + versions (ADR-004),
- `feature_ids` / `label_ids` + registry versions (ADR-005),
- `rule_set` (ASTs, ADR-006),
- optimizer config, validation config, seeds, git commit, runtime versions.

### Execution Rules

1. Deterministic: fixed seeds; no wall-clock dependence; no network during execution.
2. Stateless engines (ADR-001): inputs in → artifacts out; nothing mutated.
3. Outputs: `CandidateResult` per candidate + full `ExperimentResult`.

### Validation Gauntlet (for Candidates)

Promotion to Edge requires ALL of:
1. **Walk-forward validation** on in-sample folds;
2. **Purged** fold boundaries (no leakage between train/validation);
3. **Out-of-sample test** on the sacred held-out set (used exactly once, at the end);
4. **Stability tests** (regime/segment breakdown, parameter sensitivity);
5. **Minimum viability:** sample size, unique symbols, months of coverage — thresholds defined in `docs/specifications/protocols/experiment.md`.

### Anti-Overfitting Doctrine

- The OOS set is sacrosanct: any process that touches it before the final validation is tainted.
- Multiple-testing correction (White/Hansen reality check) is applied when many candidates are screened.
- No manual re-runs to "improve" results after seeing OOS.

### Registry & Lifecycle

Experiments follow the lifecycle in ADR-002A. Every experiment (including FAILED) is recorded in the AKB with full provenance.

## Consequences

- **Positive:** Comparable, reproducible, trustworthy research; false discoveries suppressed; every Edge has an auditable birth certificate.
- **Negative:** Heavy declaration overhead; slower iteration. Accepted — quality priority 1–4 (ADR-001B).

## Alternatives Considered

- **Ad hoc research scripts:** Rejected — irreproducible, incomparable.
- **Single global backtest:** Rejected — no OOS discipline, no candidate screening statistics.

## Migration Path

None for v1.0.
