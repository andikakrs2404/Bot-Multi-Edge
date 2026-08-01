"""AlphaOS ReplayEngine: read-only ledger views.

Reconstructs Decision/Portfolio/Edge timelines from a ProductionLedger
for audit, debugging, and forensics. NOT a simulator: never recalculates
signals, rules, or evidence, and never mutates the ledger.
"""

from __future__ import annotations

from dataclasses import dataclass

from .ledger import LedgerEntry, ProductionLedger


@dataclass(frozen=True, slots=True)
class DecisionEvent:
    recorded_at: object
    decision_id: str
    decision: str
    confidence: float
    portfolio_id: str


@dataclass(frozen=True, slots=True)
class PortfolioTimeline:
    portfolio_id: str
    entries: tuple[LedgerEntry, ...]


@dataclass(frozen=True, slots=True)
class EdgeEvent:
    edge_id: str
    decision_id: str
    decision: str
    recorded_at: object


@dataclass(frozen=True, slots=True)
class EdgeTimeline:
    edge_id: str
    events: tuple[EdgeEvent, ...]


@dataclass(frozen=True, slots=True)
class ReplayResult:
    _ledger: ProductionLedger

    def decision_timeline(self, portfolio_id: str | None = None) -> tuple[DecisionEvent, ...]:
        entries = self._ledger.all()
        if portfolio_id is not None:
            entries = tuple(e for e in entries
                            if e.portfolio_id == portfolio_id)
        return tuple(
            DecisionEvent(
                recorded_at=e.recorded_at,
                decision_id=e.decision_id,
                decision=e.decision.decision,
                confidence=e.decision.confidence,
                portfolio_id=e.portfolio_id,
            )
            for e in entries
        )

    def portfolio_timeline(self) -> tuple[PortfolioTimeline, ...]:
        grouped: dict[str, list[LedgerEntry]] = {}
        for e in self._ledger.all():
            grouped.setdefault(e.portfolio_id, []).append(e)
        return tuple(
            PortfolioTimeline(pid, tuple(entries))
            for pid, entries in grouped.items()
        )

    def edge_timeline(self, edge_id: str | None = None) -> tuple[EdgeTimeline, ...]:
        events = []
        for e in self._ledger.all():
            for triggered in e.decision.triggered_edges:
                if edge_id is not None and triggered != edge_id:
                    continue
                events.append(EdgeEvent(
                    edge_id=triggered,
                    decision_id=e.decision_id,
                    decision=e.decision.decision,
                    recorded_at=e.recorded_at,
                ))
        if edge_id is not None:
            return tuple(events)
        grouped: dict[str, list[EdgeEvent]] = {}
        for ev in events:
            grouped.setdefault(ev.edge_id, []).append(ev)
        return tuple(
            EdgeTimeline(eid, tuple(evs))
            for eid, evs in grouped.items()
        )


class ReplayEngine:
    def __init__(self, ledger: ProductionLedger) -> None:
        self.ledger = ledger

    def replay(self) -> ReplayResult:
        return ReplayResult(self.ledger)
