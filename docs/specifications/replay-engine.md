# Specification: Replay Engine v0.1

Derived from: ADR-002 (Ontology), ADR-001 (Determinism)
Constitution: be37bf97... (Freeze v1.0, 2026-07-29)

Status: Draft (v0.1)

## 1. Purpose

ReplayEngine reconstructs read-only views over a ProductionLedger for
audit, debugging, and forensics. It is NOT a simulator: it never
recalculates signals, rules, or evidence, and never mutates state.

## 2. Scope

Input:

```text
ProductionLedger
```

Output (read-only views):

```text
Decision Timeline   : chronological list of (ts, decision)
Portfolio Timeline  : ledger entries grouped by portfolio
Edge Timeline       : per-edge events from ledger entries
```

NOT in scope: PnL, equity curve, returns, drawdown, fills, positions,
backtesting, research replay.

## 3. Determinism

- `replay(ledger) == replay(ledger)` for identical ledgers.
- Views follow ledger insertion order exactly (append-only).
- No timestamps invented: only `LedgerEntry.recorded_at` and decision
  content are used.

## 4. Read-only

Replay never creates ProductionDecision, Signal, Edge, or any artifact.
It only reads the ledger.

## 5. Query API

- `replay() -> ReplayResult` (all views in one pass)
- `ReplayResult.decision_timeline(portfolio_id=None) -> tuple[DecisionEvent, ...]`
- `ReplayResult.portfolio_timeline() -> tuple[PortfolioTimeline, ...]`
- `ReplayResult.edge_timeline(edge_id=None) -> tuple[EdgeEvent, ...]`

`DecisionEvent`: (recorded_at, decision_id, decision, confidence,
portfolio_id)
`PortfolioTimeline`: (portfolio_id, entries)
`EdgeEvent`: (edge_id, decision_id, decision, recorded_at)

## 6. Acceptance Criteria

- replay twice → identical output
- ledger order preserved in all views
- no mutation of ledger (read-only)
- decision_timeline sorted by insertion order
- edge_timeline aggregates decisions touching each edge
- portfolio_timeline groups by portfolio
