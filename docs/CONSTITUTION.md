# AlphaOS Constitutional Package

**Version:** 1.0 (Draft — pending review & ratification)

**Date:** 2026-07-29

## Purpose

This file is the single official reference to the AlphaOS constitution. Layer 0 and Layer 1 are ratified TOGETHER as one package (ADR-001A). After ratification, no change to Layers 0–1 is permitted except via a new ADR that explicitly supersedes an existing one.

## Included ADRs

### Layer 0 — Constitution

| ID | Title | Status |
| --- | --- | --- |
| ADR-000 | Vision, Philosophy, and Invariants | Draft |
| ADR-000A | Ubiquitous Language | Draft |
| ADR-000B | System Boundaries & Trust Model | Draft |
| ADR-001 | Engineering Principles | Draft |
| ADR-001A | Decision Record Protocol | Draft |
| ADR-001B | Architectural Quality Attributes | Draft |

### Layer 1 — Domain & Contracts

| ID | Title | Status |
| --- | --- | --- |
| ADR-002 | Domain Ontology | Draft |
| ADR-002A | Domain Lifecycles | Draft |
| ADR-003 | Data Contract | Draft |
| ADR-004 | Dataset Versioning | Draft |
| ADR-005 | Registry Model (Feature & Label) | Draft |
| ADR-006 | Rule Grammar (AST) | Draft |
| ADR-007 | Experiment Protocol | Draft |
| ADR-008 | Evidence Model | Draft |
| ADR-009 | AKB Representation | Draft |

## Architectural Hash

Computed at ratification time as:

```text
SHA256( concatenation of all ratified ADR files, sorted by ID )
```

**Draft package hash (2026-07-29):**

```text
0ab1681a40bee7363d1d399eb9dbe39b9198af8da82b71a07fbbb7c055be1e08
```

**Status: PENDING RATIFICATION** — hash will be recomputed and recorded here during the Freeze Ceremony.

Every Experiment records the `constitution_hash` it ran under (ADR-007).

## Constitutional Scope Lock

During this freeze: **no new domain concepts may be added.** Only clarity fixes, contradiction repairs, and wording corrections are permitted (ADR-001A).

## Ratification Checklist

- [ ] All terms trace to ADR-000A
- [ ] No entity without ontology
- [ ] No lifecycle without ontology
- [ ] No contract without entity
- [ ] No schema without contract
- [ ] No implementation detail in Layers 0–1
- [ ] No circular ADR dependencies (DAG verified)
- [ ] Review passes: Consistency, Completeness, Minimality, Timelessness, Closure
- [ ] Architectural Hash computed and recorded
- [ ] Freeze declared: Layers 0–1 RATIFIED
