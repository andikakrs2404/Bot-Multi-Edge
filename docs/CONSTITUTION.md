# AlphaOS Constitutional Package

**Version:** 1.0

**Status:** ✅ **RATIFIED** (Constitutional Freeze declared)

**Date:** 2026-07-29

## Purpose

This file is the single official reference to the AlphaOS constitution. Layer 0 and Layer 1 are ratified TOGETHER as one package (ADR-001A). After ratification, no change to Layers 0–1 is permitted except via a new ADR that explicitly supersedes an existing one.

## Included ADRs

### Layer 0 — Constitution

| ID | Title | Status |
| --- | --- | --- |
| ADR-000 | Vision, Philosophy, and Invariants | ✅ Ratified |
| ADR-000A | Ubiquitous Language | ✅ Ratified |
| ADR-000B | System Boundaries & Trust Model | ✅ Ratified |
| ADR-001 | Engineering Principles | ✅ Ratified |
| ADR-001A | Decision Record Protocol | ✅ Ratified |
| ADR-001B | Architectural Quality Attributes | ✅ Ratified |

### Layer 1 — Domain & Contracts

| ID | Title | Status |
| --- | --- | --- |
| ADR-002 | Domain Ontology | ✅ Ratified |
| ADR-002A | Domain Lifecycles | ✅ Ratified |
| ADR-003 | Data Contract | ✅ Ratified |
| ADR-004 | Dataset Versioning | ✅ Ratified |
| ADR-005 | Registry Model (Feature & Label) | ✅ Ratified |
| ADR-006 | Rule Grammar (AST) | ✅ Ratified |
| ADR-007 | Experiment Protocol | ✅ Ratified |
| ADR-008 | Evidence Model | ✅ Ratified |
| ADR-009 | AKB Representation | ✅ Ratified |

## Architectural Hash (FINAL)

```text
be37bf97508691f93557849e1b05d7a1bf2c7be89029cc7f9dcbc77ba964d8cd
```

Computed as `SHA256( concatenation of all ratified ADR files, sorted by ID )`.

Every Experiment records the `constitution_hash` it ran under (ADR-007).

## Freeze Declaration

```text
═══════════════════════════════════════════════════
AlphaOS Constitutional Freeze v1.0
Date: 2026-07-29
Git commit: (recorded at commit time)
Reviewer: andikakrs2404
Layer 0: ✅ Ratified
Layer 1: ✅ Ratified
Architectural Hash: be37bf97...
═══════════════════════════════════════════════════
```

No implementation may change the constitutional layers without a new ADR that supersedes the old one. No new domain concepts may be added during implementation (Constitutional Scope Lock, ADR-001A).

## Ratification Checklist

- [x] All terms trace to ADR-000A
- [x] No entity without ontology
- [x] No lifecycle without ontology
- [x] No contract without entity
- [x] No schema without contract
- [x] No implementation detail in Layers 0–1
- [x] No circular ADR dependencies (DAG verified)
- [x] Review passes: Consistency, Completeness, Minimality, Timelessness, Closure
- [x] Architectural Hash computed and recorded
- [x] Freeze declared: Layers 0–1 RATIFIED
