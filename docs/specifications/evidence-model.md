# Specification: Evidence Model

Derived from: ADR-008 (Evidence Model), ADR-002 (Domain Ontology), ADR-007 (Experiment Protocol)
Constitution: be37bf97... (Freeze v1.0, 2026-07-29)

Status: Draft (v0.1)

## 1. Purpose

Evidence is what separates Knowledge from opinion (ADR-000 axiom 2).
An Evidence record binds experimental results (metrics + artifacts) to
a Candidate, gives them a reviewable lifecycle, and becomes the basis
for Edge promotion (Validator's job, later stage).

## 2. Evidence Record

```text
evidence_id      = EVID-<sha256(candidate_id + canonical metrics)[:20]>
experiment_id    # owning experiment
candidate_id     # owning candidate (traceability: Evidence → Candidate → Experiment)
edge_id          # null until promotion (Validator sets it)
metrics          # immutable dict: sample, hit_rate, ... (Validator adds PF/Sharpe)
artifacts        # tuple of artifact paths (snapshot dir, reports)
status           # GENERATED → REVIEWED → SUPPORTS | REFUTES
created_at       # UTC
```

## 3. Lifecycle

```text
GENERATED → REVIEWED → SUPPORTS
                    ↘ REFUTES
```

- GENERATED: emitted by ExperimentRunner (ADR-007).
- REVIEWED: under Validator assessment.
- SUPPORTS: metrics meet acceptance criteria → eligible for Edge promotion.
- REFUTES: metrics fail criteria → candidate rejected, evidence retained
  (negative results are knowledge too — ADR-000 axiom 1: knowledge
  evolves, never overwritten).

Transitions are forward-only; REFUTES/SUPPORTS are terminal states.

## 4. Registry

EvidenceRegistry (registry kernel, ADR-005):

- `get(evidence_id)` → ACTIVE entry
- `history(evidence_id)`
- `all_supporting()` → SUPPORTS entries
- `all_refuting()` → REFUTES entries
- one evidence_id per (candidate, metrics) — duplicates rejected

## 5. Acceptance Criteria (Validator stage defaults)

```text
sample    >= 300
hit_rate  >= 0.55
profit_factor >= 1.3      # added at Validator stage
sharpe    >= 1.2          # added at Validator stage
```

Evidence Model itself only carries metrics; the Validator Engine
(ADR-008 stage 2) applies criteria and sets SUPPORTS/REFUTES.

## 6. Retention

All evidence is retained forever (immutable, append-only). Negative
results are searchable via `all_refuting()` — they prevent re-running
failed hypotheses and document the knowledge frontier.

## 7. Acceptance Criteria (this stage)

- Evidence ID deterministic
- lifecycle GENERATED → REVIEWED → SUPPORTS | REFUTES, forward-only
- EvidenceRegistry: register/get/history/all_supporting/all_refuting
- duplicates rejected
- traceability: evidence → candidate → experiment
