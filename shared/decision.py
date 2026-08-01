"""AlphaOS ProductionDecisionEngine: Signal → Decision.

Consumes a SignalBatch (already evaluated by SignalEngine) and produces
a single auditable ProductionDecision per portfolio.

Decision mapping (v0.1):
- empty batch                → HOLD
- ≥1 LONG, 0 SHORT           → BUY
- ≥1 SHORT, 0 LONG           → SELL
- ≥1 LONG and ≥1 SHORT       → SKIP (conflicting signals)
"""

from __future__ import annotations

from .contracts import (
    Portfolio,
    ProductionDecision,
    SignalBatch,
    SignalDirection,
    content_hash,
)


class DecisionEngineError(ValueError):
    """Decision engine invariant violation."""


def decision_id(portfolio_id: str, signal_ids: tuple[str, ...], decision: str) -> str:
    return content_hash({
        "portfolio_id": portfolio_id,
        "signal_ids": sorted(signal_ids),
        "decision": decision,
    })


class ProductionDecisionEngine:
    def evaluate(self, portfolio: Portfolio, batch: SignalBatch) -> ProductionDecision:
        if batch.portfolio_id != portfolio.portfolio_id:
            raise DecisionEngineError(
                f"batch portfolio {batch.portfolio_id!r} != "
                f"portfolio {portfolio.portfolio_id!r}")

        signals = batch.signals
        for s in signals:
            if s.portfolio_id != portfolio.portfolio_id:
                raise DecisionEngineError(
                    f"signal {s.signal_id} belongs to portfolio "
                    f"{s.portfolio_id!r}, not {portfolio.portfolio_id!r}")

        edge_ids = [s.edge_id for s in signals]
        if len(set(edge_ids)) != len(edge_ids):
            raise DecisionEngineError("duplicate edge in signal batch")

        longs = [s for s in signals if s.direction == SignalDirection.LONG]
        shorts = [s for s in signals if s.direction == SignalDirection.SHORT]

        if not signals:
            decision, triggered, confidence = "HOLD", (), 0.0
        elif longs and shorts:
            decision, triggered, confidence = "SKIP", tuple(sorted(edge_ids)), 0.0
        elif longs:
            decision, triggered, confidence = (
                "BUY", tuple(s.edge_id for s in longs),
                sum(s.confidence for s in longs) / len(longs))
        else:
            decision, triggered, confidence = (
                "SELL", tuple(s.edge_id for s in shorts),
                sum(s.confidence for s in shorts) / len(shorts))

        return ProductionDecision(
            decision_id=decision_id(
                portfolio.portfolio_id, tuple(s.signal_id for s in signals), decision),
            portfolio_id=portfolio.portfolio_id,
            triggered_edges=triggered,
            decision=decision,
            confidence=confidence,
        )
