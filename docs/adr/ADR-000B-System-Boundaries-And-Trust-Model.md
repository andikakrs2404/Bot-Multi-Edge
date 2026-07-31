# ADR-000B: System Boundaries & Trust Model

- **Layer:** 0 (Constitution)
- **Status:** Ratified
- **Date:** 2026-07-29
- **Depends On:** ADR-000A

## Context

AlphaOS ingests untrusted external data and produces trustworthy internal knowledge. Without explicit boundaries and a trust hierarchy, components will consume data at the wrong trust level, silently corrupting research and production. This ADR fixes what is inside the system, what is outside, and how trust is earned.

## Decision

### System Boundaries

**External World (untrusted):** Exchange APIs, data vendors, execution venues, human operators, notification channels. Anything not defined in the AKB ecosystem is external.

**AlphaOS Core (trusted):** The engines, registries, and the AKB itself. Communication inside the Core happens only through versioned contracts.

### Trust Model — Hierarchy of Evidence

Trust is earned as data flows through the pipeline. A component may only consume data at its own trust level or higher (more validated).

| Level | Artifact | Description |
| --- | --- | --- |
| 0 | Raw Observations | Dirty, unvalidated data from external sources. |
| 1 | Versioned Dataset | Cleaned, integrity-checked, immutable, content-addressed. |
| 2 | Feature/Label Snapshot | Derived features and labels, linked to registries. |
| 3 | Experimental Results | Candidates, metrics, backtest outputs. Unproven. |
| 4 | Validated Knowledge | Edges that passed the full validation gauntlet. |
| 5 | Active Edges | Knowledge promoted for live use by Production. |

### Trust Invariant

The Production Realm may consume ONLY:
- Trust Level 4/5 (Validated/Active Edges and their parameters) from the AKB;
- Realtime Trust Level 2 feature computation.

Production is STRICTLY FORBIDDEN from consuming Levels 0, 1, or 3.

## Consequences

- **Positive:** Corruption cannot propagate across realms; production integrity is guaranteed by construction; audit paths are simple.
- **Negative:** Pipeline stages must maintain explicit provenance metadata. Slight overhead. Accepted.

## Alternatives Considered

- **Flat trust (everything internal is equal):** Rejected — experimental results would leak into production.
- **No explicit boundaries:** Rejected — scope creep would destabilize the architecture over time.

## Migration Path

None for v1.0.
