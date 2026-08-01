# Specification: Production Ledger

Derived from: ADR-002 (Ontology), ADR-001 (Determinism)
Constitution: be37bf97... (Freeze v1.0, 2026-07-29)

Status: Draft (v0.1)

## 1. Purpose

ProductionLedger persists ProductionDecisions as immutable historical
artifacts. It closes the epistemiology chain:

```text
Observation → Evidence → Knowledge → Signal → Decision → Recorded Fact
```

The ledger is the compliance/audit boundary between the Decision domain
and the (future) Execution domain.

## 2. Scope

Input:

```text
ProductionDecision
```

Output:

```text
LedgerEntry (immutable, append-only)
```

NOT in scope: execution status (EXECUTED/FILLED/FAILED), order ids,
exchange connectivity, PnL, position tracking. Those belong to a future
Execution domain with its own ADR.

## 3. LedgerEntry

```python
@dataclass(frozen=True, slots=True)
class LedgerEntry:
    entry_id: str
    decision_id: str
    portfolio_id: str
    recorded_at: datetime
    decision: ProductionDecision
```

- `entry_id`: deterministic content hash of decision_id.
- `recorded_at`: timezone-aware wall-clock of append (not part of entry_id).

## 4. Invariants

1. Append-only. No update, no delete, no reorder.
2. Duplicate decision_id rejected — a decision is recorded exactly once.
3. entry_id deterministic: identical decision → identical entry_id.
4. Queries are deterministic for a given ledger: insertion order.

## 5. Query API

- `append(decision) -> LedgerEntry`
- `by_decision(decision_id) -> LedgerEntry` (KeyError if absent)
- `by_portfolio(portfolio_id) -> tuple[LedgerEntry, ...]` (insertion order)
- `all() -> tuple[LedgerEntry, ...]` (insertion order)

## 6. Acceptance Criteria

- append stores decision; by_decision retrieves it
- entry_id deterministic across ledgers for identical decision
- duplicate decision_id rejected
- by_portfolio filters correctly
- all() returns append order (replay-ready)
