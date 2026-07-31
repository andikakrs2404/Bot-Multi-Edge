# ADR-002A: Domain Lifecycles

- **Layer:** 1 (Domain & Contracts)
- **Status:** Draft
- **Date:** 2026-07-29
- **Depends On:** ADR-002

## Context

Entities are not static. To make the AKB auditable, every aggregate root must have a defined lifecycle: legal transitions, forbidden transitions, promotion criteria, and retirement criteria. This ADR fixes the lifecycle for each aggregate root.

## Decision

Lifecycles are defined per aggregate root. All transitions must be recorded with timestamp and actor (system component or human).

### Edge

```text
DISCOVERED → OPTIMIZED → VALIDATED → ACTIVE → MONITORED
                                                  │
                                          ┌───────┴───────┐
                                          ▼               ▼
                                       DECAYED        SUPERSEDED
                                          │               │
                                          └───────┬───────┘
                                                  ▼
                                               RETIRED
```

- **Promotion criteria:** VALIDATED requires passing the full gauntlet (ADR-007/008): walk-forward, OOS, stability, minimum sample/symbols/months.
- **Retirement criteria:** DECAYED (drift score below threshold) or SUPERSEDED (replaced by a newer edge). RETIRED edges remain in the AKB as history; they are never deleted.
- **Forbidden transitions:** any backwards transition; ACTIVE without VALIDATED.

### Experiment

```text
DRAFT → QUEUED → RUNNING → COMPLETED → PROMOTED
                        │
                        ▼
                      FAILED
```

- **Promotion criteria:** COMPLETED with passing validation produces Edges.
- **Forbidden:** PROMOTED without COMPLETED; re-running a COMPLETED experiment mutates nothing (new experiment instead).

### ResearchCycle

```text
PLANNED → RUNNING → CLOSED
```

- **Invariant:** a CLOSED cycle is immutable. No experiments may be added after closure.

### Dataset

```text
CREATED → VALIDATED → REGISTERED → ACTIVE → ARCHIVED
```

- **Invariant:** ACTIVE datasets are immutable. Corrections create a new Dataset version.

### Portfolio

```text
DRAFT → BACKTESTED → APPROVED → LIVE → PAUSED → CLOSED
```

- **Invariant:** only ACTIVE Edges may be allocated.

### ProductionDecision

```text
FORMED → VALIDATED → EXECUTED → SETTLED
                        │
                        ▼
                     REJECTED
```

- **Invariant:** every decision records the PortfolioID and triggered EdgeIDs at FORMED time.

## Consequences

- **Positive:** Uniform, auditable entity behavior; simple monitoring (every edge knows where it is and why).
- **Negative:** State machines add ceremony to CRUD-like operations. Accepted.

## Alternatives Considered

- **Stateless entities (no lifecycle):** Rejected — drift and retirement become untraceable.

## Migration Path

None for v1.0.
