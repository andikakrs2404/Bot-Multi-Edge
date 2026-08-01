"""AlphaOS ProductionLedger: Decision → Immutable Recorded Fact.

Append-only immutable store of ProductionDecisions. Closes the
epistemiology chain: Observation → Evidence → Knowledge → Signal →
Decision → Recorded Fact.

Execution state (EXECUTED/FILLED/FAILED), order ids, exchange
connectivity, PnL belong to a future Execution domain — NOT here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from .contracts import ProductionDecision, content_hash, utcnow


@dataclass(frozen=True, slots=True)
class LedgerEntry:
    entry_id: str
    decision_id: str
    portfolio_id: str
    recorded_at: datetime
    decision: ProductionDecision


class ProductionLedger:
    """Append-only ledger. No update, no delete."""

    def __init__(self) -> None:
        self._entries: list[LedgerEntry] = []
        self._by_decision: dict[str, LedgerEntry] = {}

    def append(self, decision: ProductionDecision) -> LedgerEntry:
        if decision.decision_id in self._by_decision:
            raise ValueError(
                f"duplicate decision: {decision.decision_id}")
        entry_id = content_hash({"decision_id": decision.decision_id})
        entry = LedgerEntry(
            entry_id=entry_id,
            decision_id=decision.decision_id,
            portfolio_id=decision.portfolio_id,
            recorded_at=utcnow(),
            decision=decision,
        )
        self._entries.append(entry)
        self._by_decision[decision.decision_id] = entry
        return entry

    def by_decision(self, decision_id: str) -> LedgerEntry:
        return self._by_decision[decision_id]

    def by_portfolio(self, portfolio_id: str) -> tuple[LedgerEntry, ...]:
        return tuple(e for e in self._entries
                     if e.portfolio_id == portfolio_id)

    def all(self) -> tuple[LedgerEntry, ...]:
        return tuple(self._entries)
