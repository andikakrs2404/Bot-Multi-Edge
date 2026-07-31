# ADR-003: Data Contract

- **Layer:** 1 (Domain & Contracts)
- **Status:** Draft
- **Date:** 2026-07-29
- **Depends On:** ADR-002A

## Context

Engines communicate exclusively through artifacts. For artifacts to be trustworthy, their structure must be contractually fixed. This ADR establishes the principle and the taxonomy of data contracts; the exact field-level schemas live in `docs/specifications/contracts/`.

## Decision

### Principles

1. Every artifact exchanged between engines conforms to a versioned **Data Contract**.
2. A Data Contract defines: name, version, field list with types, invariants, and owner ADR.
3. Contracts are immutable once RATIFIED. Evolution = new contract version + migration path.
4. No engine may read an artifact whose contract version it does not declare support for.

### Contract Taxonomy

| Contract Family | Artifacts | Trust Level |
| --- | --- | --- |
| Raw | `RawObservation`, `RawCandle`, `RawOI`, `RawFunding`, `RawLiquidation` | 0 |
| Dataset | `VersionedDataset` (manifest + parquet set) | 1 |
| Snapshot | `FeatureSnapshot`, `LabelSnapshot` | 2 |
| Experiment | `ExperimentConfig`, `ExperimentResult`, `CandidateResult` | 3 |
| Evidence | `ValidationReport`, `StabilityReport`, `OOSReport` | 4 |
| Knowledge | `EdgeRecord`, `PortfolioRecord`, `ProductionDecisionRecord` | 4–5 |

### Field-Level Schemas

Field-level schemas (types, units, nullability) are specified in:
- `docs/specifications/contracts/raw.md`
- `docs/specifications/contracts/dataset.md`
- `docs/specifications/contracts/snapshot.md`
- `docs/specifications/contracts/experiment.md`
- `docs/specifications/contracts/evidence.md`
- `docs/specifications/contracts/knowledge.md`

Schema files are versioned and MUST declare the ADR they derive from.

## Consequences

- **Positive:** Engines can be built independently against stable contracts; schema evolution is auditable; trust levels are enforced by contract.
- **Negative:** Schema changes require contract version bumps. Accepted.

## Alternatives Considered

- **Schema-free (dicts/JSON ad hoc):** Rejected — silently breaks reproducibility and auditability.
- **Single mega-contract:** Rejected — couples unrelated artifacts.

## Migration Path

Contract evolution: new version, dual-write during transition, deprecate old version after one ResearchCycle.
