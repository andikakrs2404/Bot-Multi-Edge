# ADR Coverage Matrix

Constitution: be37bf97508691f93557849e1b05d7a1bf2c7be89029cc7f9dcbc77ba964d8cd
Freeze v1.0 (L0+L1) — 2026-07-29
Generated: 2026-08-01 (post ProductionLedger, 232 tests)

Maps every ratified ADR to its implementation module and test coverage.
Baseline before Replay Engine / Execution domain work.

## Layer 0 — Vision & Philosophy

| ADR | Title | Status | Module | Tests | Notes |
|-----|-------|--------|--------|-------|-------|
| ADR-000 | Vision, Philosophy, Invariants | ✅ | contracts.py (CONSTITUTION_HASH) | — | Constitution hash enforced in contracts |
| ADR-000A | Ubiquitous Language | ✅ | docs/specifications/* | — | Naming: Edge/Evidence/Signal/Decision |
| ADR-000B | System Boundaries & Trust Model | ✅ | fail-closed engines (signal.py, decision.py) | test_signal, test_decision | Missing edge/rule/feature → exception, never silent skip |

## Layer 1 — Engineering Principles

| ADR | Title | Status | Module | Tests | Notes |
|-----|-------|--------|--------|-------|-------|
| ADR-001 | Engineering Principles | ✅ | contracts.py (content_hash, make_id) | test_contracts | Deterministic content-addressed IDs |
| ADR-001A | Decision Record Protocol | ✅ | docs/adr/ADR-001A | — | This matrix is a product of it |
| ADR-001B | Architectural Quality Attributes | ✅ | — | — | Non-functional: immutability, reproducibility |

## Layer 1 — Domain Ontology & Lifecycles

| ADR | Title | Status | Module | Tests | Notes |
|-----|-------|--------|--------|-------|-------|
| ADR-002 | Domain Ontology | ✅ | contracts.py | test_contracts, test_akb | Dataset, Feature, Rule, Experiment, Evidence, Edge, Portfolio, ProductionDecision |
| ADR-002A | Domain Lifecycles | ✅ | contracts.py, activation.py, registry.py | test_activation, test_registry | Edge lifecycle DISCOVERED→…→RETIRED; ActivationRecord/DecayRecord |
| ADR-003 | Data Contract | ✅ | contracts.py, runtime.py | test_runtime | MarketSnapshot = runtime artifact (shared/runtime.py), NOT ontology |
| ADR-004 | Dataset Versioning | ✅ | contracts.py (content addressing) | test_contracts | Dataset id + deterministic artifacts |
| ADR-005 | Registry Model | ✅ | registry.py, registries.py | test_registry | Registry, RegistryEntry, ACTIVE/SUPERSEDED/ARCHIVED |
| ADR-006 | Rule Grammar | ✅ | rules.py | test_rules | AST: Comparison/And/Or/Not; canonicalize; evaluate |
| ADR-007 | Experiment Protocol | ✅ | experiment.py | test_experiment | Experiment artifact; reproducible protocol |
| ADR-008 | Evidence Model | ✅ | evidence.py | test_evidence | Evidence, EvidenceStatus (SUPPORTS/REFUTES/…) |
| ADR-009 | AKB Representation | ✅ | akb.py | test_akb | Graph: NodeType, RelationshipType, trace queries |

## Layer 2 — Engines (spec-first, TDD)

| Spec | Engine | Module | Tests | Status |
|------|--------|--------|-------|--------|
| dataset/feature pipeline | RawDataEngine, FeatureFactory | raw_data_engine.py, feature_factory.py, features.py | test_features | ✅ (research) |
| validator-engine.md | ValidatorEngine | validator.py | test_validator | ✅ Evidence→Edge(VALIDATED) |
| activation-engine.md | ActivationEngine | activation.py | test_activation | ✅ Edge(ACTIVE) governance |
| portfolio.md | PortfolioBuilder | portfolio.py | test_portfolio | ✅ ACTIVE-only, EQUAL_WEIGHT |
| signal-engine.md | SignalEngine | signal.py | test_signal | ✅ Knowledge→SignalBatch |
| production-decision-engine.md | ProductionDecisionEngine | decision.py | test_decision | ✅ SignalBatch→ProductionDecision |
| production-ledger.md | ProductionLedger | ledger.py | test_ledger | ✅ Decision→LedgerEntry |

## Gaps (tracked, not blocking)

| Area | Status | Note |
|------|--------|------|
| Relationship as first-class runtime entity | ⚠️ partial | ADR-002 relationships live in AKB graph (akb.py) with RelationshipType, but domain objects still carry FK-style ids (Edge.experiment_id, DecisionSignal.portfolio_id). Acceptable: FK = denormalized provenance, graph = navigable structure. |
| ProductionDecision lifecycle | ⚠️ not formal | Decision goes straight to ledger; no CREATED/RECORDED states. Deliberate: execution state belongs to future Execution domain ADR. |
| Screener V1 ADRs (docs/architecture/) | separate | ADR-001..012 there belong to Screener V1 (features/), NOT this constitution. Do not merge. |

## Summary

- ADR-000..009: **all implemented**, 1 partial (Relationship first-class), 1 deferred (Decision lifecycle).
- Engines: 7 spec-first engines, all green (232 tests).
- Next: Replay Engine (audit timeline), then Execution domain (new ADR).

## Regeneration

Update this file when:
- a new ADR is ratified
- an engine module changes scope
- test count shifts materially
