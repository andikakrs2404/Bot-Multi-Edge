# AlphaOS Domain Map v1

Constitution: be37bf97508691f93557849e1b05d7a1bf2c7be89029cc7f9dcbc77ba964d8cd
Freeze v1.0 — 2026-07-29
Generated: 2026-08-01 (post ReplayEngine, 240 tests)

Maps every domain of AlphaOS: what exists today (implemented, ADR-ratified)
and what is planned (ADR required before code).

## Implemented Domains

### Research Domain (Layer 1 — Knowledge Creation)

```text
Dataset → Feature → Rule → Experiment → Evidence → Validator → Edge
```

| Concept | Module | ADR | Status |
|---------|--------|-----|--------|
| Dataset | contracts.py | ADR-004 | ✅ |
| Feature | features.py, feature_factory.py | ADR-003 | ✅ |
| Rule | rules.py | ADR-006 | ✅ |
| Experiment | experiment.py | ADR-007 | ✅ |
| Evidence | evidence.py | ADR-008 | ✅ |
| Edge (VALIDATED) | validator.py | ADR-002A | ✅ |

### Knowledge Domain (Layer 1 — Governance)

```text
Edge(VALIDATED) → Activation → Edge(ACTIVE)
```

| Concept | Module | ADR | Status |
|---------|--------|-----|--------|
| ActivationRecord / DecayRecord | activation.py | ADR-002A | ✅ |
| Edge lifecycle | contracts.py, registry.py | ADR-002A | ✅ |

### Production Domain (Layer 2 — Knowledge Consumption)

```text
Portfolio → Signal → Decision
```

| Concept | Module | ADR | Status |
|---------|--------|-----|--------|
| Portfolio | portfolio.py | ADR-002 | ✅ |
| SignalBatch / DecisionSignal | signal.py | ADR-002 | ✅ |
| ProductionDecision | decision.py | ADR-002 | ✅ |

### Audit Domain (Layer 3 — Auditability)

```text
Ledger → Replay
```

| Concept | Module | ADR | Status |
|---------|--------|-----|--------|
| ProductionLedger | ledger.py | ADR-002 | ✅ |
| ReplayEngine | replay.py | ADR-002 | ✅ |

## Future Domains (ADR required before implementation)

### Execution Domain

```text
OrderIntent → Order → ExecutionReport → Position
```

Boundaries:

- MAY read: ProductionDecision
- MUST NOT read: Experiment, Evidence, Dataset, Feature
- Invariants: OrderIntent immutable; Order born from one Decision;
  ExecutionReport born from one Order; Position derived from
  ExecutionReports.
- ADR-010 (draft) required before code.

### Feedback Domain

```text
Decision → Outcome → Feedback → Evidence
```

Purpose: knowledge evolution ("Knowledge Evolves; It Is Never
Overwritten"). Outcomes feed revalidation, drift detection, EdgeDecay.

- ADR-011 (draft) required before code.

## Dependency Direction (ADR-001 principle 7)

```text
Audit → Production → Knowledge → Research
```

Each layer reads only from layers below. No upward reads. Execution
Domain will read ProductionDecision only; Feedback Domain will write
Evidence (research) but read Production.

## Gap Status

| Gap | Status |
|-----|--------|
| Relationship first-class runtime entity | ⚠️ partial (deferred, candidate ADR-010/011) |
| ProductionDecision lifecycle | ⚠️ deferred to Execution Domain |
| Feedback loop (outcome → evidence) | 🔴 not started, ADR-011 |

## Summary

AlphaOS Core v1.0 = COMPLETE (Research + Knowledge + Production + Audit).
Execution & Feedback = NOT APPROVED FOR IMPLEMENTATION, ADR required.
