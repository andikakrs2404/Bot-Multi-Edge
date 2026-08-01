# Specification: Production Decision Engine v0.1

Derived from: ADR-002 (Ontology), ADR-001 (Determinism)
Constitution: be37bf97... (Freeze v1.0, 2026-07-29)

Status: Draft (v0.1)

## 1. Purpose

ProductionDecisionEngine consumes a SignalBatch (already evaluated) and
produces a single auditable ProductionDecision per portfolio. Rule
evaluation is NOT repeated here — SignalEngine owns that.

## 2. Scope

Input:

```text
Portfolio
SignalBatch
```

Output:

```text
ProductionDecision
```

NOT in scope: voting systems, confidence scoring, position sizing,
order execution, conflict resolution beyond SKIP.

## 3. Decision mapping (v0.1)

| SignalBatch              | Decision |
|--------------------------|----------|
| empty                    | HOLD     |
| ≥1 LONG, 0 SHORT         | BUY      |
| ≥1 SHORT, 0 LONG         | SELL     |
| ≥1 LONG and ≥1 SHORT     | SKIP (conflicting signals) |

Confidence:

- BUY/SELL: mean confidence of contributing signals (deterministic).
- HOLD/SKIP: 0.0.

## 4. Traceability

ProductionDecision carries `portfolio_id` + `triggered_edges` (sorted
edge_ids of contributing signals) so each decision traces back to
portfolio → signals → edges → experiments → rules.

## 5. Invariants

1. Portfolio of the decision must match the SignalBatch's portfolio_id.
2. All signals in the batch must belong to the portfolio
   (portfolio_id match) — else error.
3. Signals with duplicate edge_id in one batch → error (each edge at
   most one signal per snapshot).
4. decision_id deterministic: content hash over portfolio_id,
   sorted signal_ids, decision.

## 6. Acceptance Criteria

- empty batch → HOLD, triggered_edges empty
- all LONG → BUY
- all SHORT → SELL
- mixed LONG+SHORT → SKIP
- deterministic decision_id for identical inputs
- portfolio_id mismatch (batch vs portfolio) → error
- duplicate edge in batch → error
