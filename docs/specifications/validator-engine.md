# Specification: Validator Engine

Derived from: ADR-000B (Trust Model), ADR-002/002A (Edge lifecycle), ADR-005 (Registry), ADR-008 (Evidence), ADR-009 (AKB)
Constitution: be37bf97... (Freeze v1.0, 2026-07-29)

Status: Draft (v0.1)

## 1. Purpose

Validator Engine is the first component that converts Evidence into
Knowledge (Edge):

```text
Evidence(SUPPORTS)
  ↓
ValidationPolicy
  ↓
Verdict
  ↓
Edge(VALIDATED)
```

It does NOT discover rules, run experiments, run backtests, activate
edges, allocate portfolios, or make production decisions.

## 2. Input Contract

Validator only consumes:

```text
Evidence.status == SUPPORTS
```

It must reject:

```text
GENERATED
REVIEWED
REFUTES
```

## 3. ValidationPolicy

Policy is explicit, immutable, and traceable:

```text
policy_id
min_sample
min_hit_rate
min_profit_factor
min_sharpe
```

Multiple policies may exist (`validator_policy_v1`, `v2`, `v3`).
No threshold is hidden in ValidatorEngine.

## 4. Edge Creation

Promotion creates:

```text
Edge(
  edge_id,
  rule_id,
  experiment_id,
  supported_by=(EvidenceID, ...),
  status=VALIDATED,
)
```

`supported_by` is 1:N EvidenceIDs. Evidence records must all point to
the same candidate/experiment lineage and pass the active policy.

## 5. Edge Lifecycle

Validator outputs:

```text
VALIDATED
```

not ACTIVE. Activation is Portfolio/Production governance later.

Minimal lifecycle:

```text
DISCOVERED → VALIDATED → ACTIVE → DECAYED → RETIRED
```

## 6. Registry

Validator registers the promoted Edge into EdgeRegistry.

Required query helpers:

```text
all_validated()
all_active()
all_decayed()
```

Duplicate edge promotion is rejected by registry identity.

## 7. AKB Integration

Promotion writes graph facts:

```text
Edge node
Edge --SUPPORTED_BY--> Evidence     (1:N)
Evidence --REFERENCES--> Candidate
Evidence --REFERENCES--> Experiment
```

Traceability must answer:

```text
EdgeID → EvidenceID[] → CandidateID → ExperimentID → DatasetID
ProductionDecisionID → PortfolioID → EdgeID → EvidenceID[]
```

## 8. Acceptance Criteria

- SUPPORTS Evidence can promote to Edge(VALIDATED)
- non-SUPPORTS Evidence rejected
- ValidationPolicy thresholds enforced
- supported_by multi-evidence works
- EdgeRegistry register/get/history/all_validated/all_active/all_decayed works
- duplicate edge rejected
- AKB trace Edge → Evidence → Candidate → Experiment → Dataset works
- no ACTIVE edge produced by Validator
