"""Tests for AlphaOS ProductionDecisionEngine (Signal → Decision)."""

from datetime import datetime, timezone

import pytest

from shared.contracts import (
    DecisionSignal,
    Portfolio,
    PortfolioAllocation,
    PortfolioStatus,
    ProductionDecision,
    SignalBatch,
    SignalDirection,
    make_batch_id,
    make_signal_id,
)
from shared.decision import (
    DecisionEngineError,
    ProductionDecisionEngine,
    decision_id,
)
from shared.runtime import MarketSnapshot, make_snapshot_id


TS = datetime(2026, 7, 31, 12, 0, 0, tzinfo=timezone.utc)


def snap() -> MarketSnapshot:
    return MarketSnapshot(
        snapshot_id=make_snapshot_id("BTCUSDT", TS, {"RSI_14": 75.0}),
        symbol="BTCUSDT",
        timestamp=TS,
        feature_values={"RSI_14": 75.0},
    )


def portfolio(pid="PORT-1") -> Portfolio:
    return Portfolio(
        portfolio_id=pid,
        policy_id="policy_v1",
        allocations=(PortfolioAllocation("EDGE-A", 1.0, SignalDirection.LONG),),
        status=PortfolioStatus.LIVE,
    )


def sig(edge_id: str, direction: SignalDirection, pid="PORT-1",
        confidence=0.8) -> DecisionSignal:
    return DecisionSignal(
        signal_id=make_signal_id(edge_id, pid, snap().snapshot_id, "BTCUSDT", direction),
        edge_id=edge_id,
        rule_id=f"RULE-{edge_id}",
        experiment_id="EXP-1",
        portfolio_id=pid,
        symbol="BTCUSDT",
        market_snapshot_id=snap().snapshot_id,
        direction=direction,
        confidence=confidence,
    )


def batch(signals: tuple[DecisionSignal, ...], pid="PORT-1") -> SignalBatch:
    return SignalBatch(
        batch_id=make_batch_id(pid, snap().snapshot_id,
                               tuple(s.signal_id for s in signals)),
        portfolio_id=pid,
        market_snapshot_id=snap().snapshot_id,
        signals=signals,
    )


class TestDecisionMapping:
    def test_empty_batch_hold(self):
        engine = ProductionDecisionEngine()
        d = engine.evaluate(portfolio(), batch(()))

        assert isinstance(d, ProductionDecision)
        assert d.decision == "HOLD"
        assert d.triggered_edges == ()
        assert d.confidence == 0.0

    def test_all_long_buy(self):
        engine = ProductionDecisionEngine()
        d = engine.evaluate(portfolio(), batch((sig("EDGE-A", SignalDirection.LONG),)))

        assert d.decision == "BUY"
        assert d.triggered_edges == ("EDGE-A",)

    def test_all_short_sell(self):
        engine = ProductionDecisionEngine()
        d = engine.evaluate(portfolio(), batch((sig("EDGE-A", SignalDirection.SHORT),)))

        assert d.decision == "SELL"
        assert d.triggered_edges == ("EDGE-A",)

    def test_mixed_long_short_skip(self):
        engine = ProductionDecisionEngine()
        s = (
            sig("EDGE-A", SignalDirection.LONG),
            sig("EDGE-B", SignalDirection.SHORT),
        )
        d = engine.evaluate(portfolio(), batch(s))

        assert d.decision == "SKIP"
        assert d.triggered_edges == ("EDGE-A", "EDGE-B")

    def test_confidence_is_mean_of_signals(self):
        engine = ProductionDecisionEngine()
        s = (
            sig("EDGE-A", SignalDirection.LONG, confidence=0.6),
            sig("EDGE-B", SignalDirection.LONG, confidence=0.8),
        )
        d = engine.evaluate(portfolio(), batch(s))

        assert d.decision == "BUY"
        assert d.confidence == pytest.approx(0.7)


class TestDeterminism:
    def test_identical_inputs_identical_decision_id(self):
        engine = ProductionDecisionEngine()
        s = (sig("EDGE-A", SignalDirection.LONG),)
        d1 = engine.evaluate(portfolio(), batch(s))
        d2 = engine.evaluate(portfolio(), batch(s))

        assert d1.decision_id == d2.decision_id
        assert d1.decision_id == decision_id(
            "PORT-1", tuple(x.signal_id for x in s), "BUY")


class TestErrors:
    def test_portfolio_id_mismatch_rejected(self):
        engine = ProductionDecisionEngine()
        with pytest.raises(DecisionEngineError, match="portfolio"):
            engine.evaluate(portfolio("PORT-1"), batch((sig("EDGE-A", SignalDirection.LONG),), pid="PORT-2"))

    def test_signal_portfolio_mismatch_rejected(self):
        engine = ProductionDecisionEngine()
        s = (
            sig("EDGE-A", SignalDirection.LONG, pid="PORT-1"),
            sig("EDGE-B", SignalDirection.LONG, pid="PORT-2"),
        )
        with pytest.raises(DecisionEngineError, match="portfolio"):
            engine.evaluate(portfolio("PORT-1"), batch(s, pid="PORT-1"))

    def test_duplicate_edge_rejected(self):
        engine = ProductionDecisionEngine()
        s = (
            sig("EDGE-A", SignalDirection.LONG),
            sig("EDGE-A", SignalDirection.LONG),
        )
        with pytest.raises(DecisionEngineError, match="duplicate"):
            engine.evaluate(portfolio(), batch(s))
