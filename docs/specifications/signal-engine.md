# Specification: Signal Engine

Derived from: ADR-001 (Determinism), ADR-006 (Rule Grammar), ADR-002 (Ontology)
Constitution: be37bf97... (Freeze v1.0, 2026-07-29)

Status: Draft (v0.1)

## 1. Purpose

Signal Engine translates Portfolio knowledge + live MarketSnapshot into
a SignalBatch of DecisionSignals. It is the Knowledge → Signal layer
of the epistemiology chain: Observation → Evidence → Knowledge → Signal
→ Decision → Action.

## 2. Scope

Input:

```text
Portfolio
MarketSnapshot
```

Output:

```text
SignalBatch
```

NOT in scope: confidence scoring, signal ranking, conflict resolution,
position sizing, portfolio optimization, ProductionDecision.

## 3. No-signal convention

```text
No signal == absence of DecisionSignal
```

A rule that evaluates FALSE produces NO DecisionSignal. There is no
NEUTRAL direction. An empty SignalBatch means neutral.

## 4. Rule evaluation

Rules are evaluated against the snapshot's feature_values converted to
FeatureValue(value=v) (percentile/zscore NaN).

Threshold scope (v0.1):

- const thresholds (e.g. `GT RSI_14 70`): supported.
- pct/z thresholds (P80, Z1.5): NaN comparison → FALSE, not yet supported.

A missing feature in the snapshot raises an error (fail-closed, no
silent skip).

## 5. Traceability

Every DecisionSignal must be traceable:

```text
signal → edge → rule + experiment
```

SignalEngine reads Edge metadata (rule_id, experiment_id) from the
EdgeRegistry and the Rule AST from the RuleRegistry. It never accepts
bare edge_ids.

## 6. Determinism

Identical (portfolio, snapshot) inputs produce identical:

- signal_ids (content hash over edge_id, portfolio_id, snapshot_id, symbol, direction)
- batch_id (content hash over portfolio_id, snapshot_id, sorted signal_ids)

Signals are sorted by edge_id.

## 7. Invariants

1. Portfolio edges must all be ACTIVE → else error.
2. Missing rule/edge metadata → error.
3. Missing feature in snapshot → error.
4. Signals sorted by edge_id; batch_id deterministic.

## 8. Acceptance Criteria

- Rule TRUE + LONG allocation → 1 DecisionSignal LONG
- Rule TRUE + SHORT allocation → 1 DecisionSignal SHORT
- Rule FALSE → no signal for that edge
- Mixed TRUE/FALSE → only TRUE signals, sorted by edge_id
- Portfolio with non-ACTIVE edge → error
- Missing rule/experiment metadata → error
- Missing snapshot feature → error
- Identical inputs → identical signal_ids + batch_id
