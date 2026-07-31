# AlphaOS Architectural Decision Records (ADRs)

This directory contains the architectural decisions that form the constitution of AlphaOS. Once RATIFIED, an ADR is never edited; changes are made by superseding it with a new ADR (ADR-001A).

**Status legend:** DRAFT → PROPOSED → RATIFIED → SUPERSEDED

## Constitutional Package v1.0

Package index & ratification checklist: [`docs/CONSTITUTION.md`](../CONSTITUTION.md)

### Layer 0 — Constitution

| ID | Title | Status | Depends On |
| --- | --- | --- | --- |
| [ADR-000](ADR-000-Vision-Philosophy-And-Invariants.md) | Vision, Philosophy, and Invariants | Draft | — |
| [ADR-000A](ADR-000A-Ubiquitous-Language.md) | Ubiquitous Language | Draft | ADR-000 |
| [ADR-000B](ADR-000B-System-Boundaries-And-Trust-Model.md) | System Boundaries & Trust Model | Draft | ADR-000A |
| [ADR-001](ADR-001-Engineering-Principles.md) | Engineering Principles | Draft | ADR-000B |
| [ADR-001A](ADR-001A-Decision-Record-Protocol.md) | Decision Record Protocol | Draft | ADR-001 |
| [ADR-001B](ADR-001B-Architectural-Quality-Attributes.md) | Architectural Quality Attributes | Draft | ADR-001A |

### Layer 1 — Domain & Contracts

| ID | Title | Status | Depends On |
| --- | --- | --- | --- |
| [ADR-002](ADR-002-Domain-Ontology.md) | Domain Ontology | Draft | Layer 0 |
| [ADR-002A](ADR-002A-Domain-Lifecycles.md) | Domain Lifecycles | Draft | ADR-002 |
| [ADR-003](ADR-003-Data-Contract.md) | Data Contract | Draft | ADR-002A |
| [ADR-004](ADR-004-Dataset-Versioning.md) | Dataset Versioning | Draft | ADR-003 |
| [ADR-005](ADR-005-Registry-Model.md) | Registry Model (Feature & Label) | Draft | ADR-004 |
| [ADR-006](ADR-006-Rule-Grammar.md) | Rule Grammar (AST) | Draft | ADR-005 |
| [ADR-007](ADR-007-Experiment-Protocol.md) | Experiment Protocol | Draft | ADR-006 |
| [ADR-008](ADR-008-Evidence-Model.md) | Evidence Model | Draft | ADR-007 |
| [ADR-009](ADR-009-AKB-Representation.md) | AKB Representation | Draft | ADR-008 |

### Dependency Rules

- ADRs may reference only the same layer or layers above them (Layer N → Layer ≤ N).
- The dependency graph is a DAG; circular dependencies are forbidden (linter-enforced at review).

### Supporting Documents

- Specifications (WHAT): [`docs/specifications/`](../specifications/) — field-level schemas, protocols, metric formulas.
- Standards (HOW): [`docs/standards/`](../standards/) — naming, git, style conventions (changeable, not constitutional).
