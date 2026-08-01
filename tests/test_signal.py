"""Tests for AlphaOS Signal Engine (Knowledge → Signal)."""

from datetime import datetime, timezone

import pytest

from shared.akb import AKB, NodeType
from shared.contracts import (
    DecisionSignal,
    Edge,
    EdgeStatus,
    PortfolioAllocation,
    PortfolioStatus,
    Rule,
    SignalBatch,
    SignalDirection,
    make_batch_id,
    make_signal_id,
)
from shared.portfolio import Portfolio, PortfolioPolicy, PortfolioBuilder
from shared.registries import EdgeRegistry, RuleRegistry, PortfolioRegistry
from shared.rules import parse
from shared.runtime import MarketSnapshot, make_snapshot_id
from shared.signal import SignalEngine, SignalEngineError


TS = datetime(2026, 7, 31, 12, 0, 0, tzinfo=timezone.utc)


def rule(rule_id: str, text: str) -> Rule:
    return Rule(rule_id=rule_id, ast=parse(text).to_text())


def edge(edge_id: str, rule_id: str, status=EdgeStatus.ACTIVE) -> Edge:
    return Edge(edge_id=edge_id, rule_id=rule_id, experiment_id="EXP-1",
                status=status)


def snapshot(features: dict[str, float]) -> MarketSnapshot:
    return MarketSnapshot(
        snapshot_id=make_snapshot_id("BTCUSDT", TS, features),
        symbol="BTCUSDT",
        timestamp=TS,
        feature_values=features,
    )


def build(edges: list[Edge], rules: list[Rule],
          allocs: list[tuple[str, SignalDirection]]):
    ereg, rreg, preg = EdgeRegistry(), RuleRegistry(), PortfolioRegistry()
    for e in edges:
        ereg.register(e)
    for r in rules:
        rreg.register(r)
    akb = AKB()
    for e in edges:
        akb.add_node(NodeType.EDGE, e.edge_id, e)
    for r in rules:
        akb.add_node(NodeType.RULE, r.rule_id, r)
    policy = PortfolioPolicy("policy_v1", max_edges=10)
    portfolio = PortfolioBuilder(policy, ereg, preg, akb).create(allocs)
    engine = SignalEngine(ereg, rreg)
    return engine, portfolio


class TestSignalGeneration:
    def test_rule_true_long_produces_signal(self):
        r = rule("RULE-1", "(GT RSI_14 70)")
        e = edge("EDGE-A", "RULE-1")
        engine, portfolio = build([e], [r], [("EDGE-A", SignalDirection.LONG)])

        batch = engine.evaluate(portfolio, snapshot({"RSI_14": 75.0}))

        assert isinstance(batch, SignalBatch)
        assert len(batch.signals) == 1
        s = batch.signals[0]
        assert s.edge_id == "EDGE-A"
        assert s.rule_id == "RULE-1"
        assert s.experiment_id == "EXP-1"
        assert s.portfolio_id == portfolio.portfolio_id
        assert s.symbol == "BTCUSDT"
        assert s.market_snapshot_id == snapshot({"RSI_14": 75.0}).snapshot_id
        assert s.direction == SignalDirection.LONG

    def test_rule_true_short_produces_signal(self):
        r = rule("RULE-1", "(GT RSI_14 70)")
        e = edge("EDGE-A", "RULE-1")
        engine, portfolio = build([e], [r], [("EDGE-A", SignalDirection.SHORT)])

        batch = engine.evaluate(portfolio, snapshot({"RSI_14": 75.0}))

        assert batch.signals[0].direction == SignalDirection.SHORT

    def test_rule_false_no_signal(self):
        r = rule("RULE-1", "(GT RSI_14 70)")
        e = edge("EDGE-A", "RULE-1")
        engine, portfolio = build([e], [r], [("EDGE-A", SignalDirection.LONG)])

        batch = engine.evaluate(portfolio, snapshot({"RSI_14": 50.0}))

        assert batch.signals == ()

    def test_mixed_rules_sorted_by_edge_id(self):
        r1 = rule("RULE-1", "(GT RSI_14 70)")
        r2 = rule("RULE-2", "(GT EMA_20 50)")
        e1 = edge("EDGE-B", "RULE-1")
        e2 = edge("EDGE-A", "RULE-2")
        engine, portfolio = build(
            [e1, e2],
            [r1, r2],
            [("EDGE-B", SignalDirection.LONG), ("EDGE-A", SignalDirection.SHORT)],
        )

        batch = engine.evaluate(portfolio, snapshot({"RSI_14": 75.0, "EMA_20": 100.0}))

        assert [s.edge_id for s in batch.signals] == ["EDGE-A", "EDGE-B"]


class TestDeterminism:
    def test_identical_inputs_identical_ids(self):
        r = rule("RULE-1", "(GT RSI_14 70)")
        e = edge("EDGE-A", "RULE-1")
        engine, portfolio = build([e], [r], [("EDGE-A", SignalDirection.LONG)])
        snap = snapshot({"RSI_14": 75.0})

        b1 = engine.evaluate(portfolio, snap)
        b2 = engine.evaluate(portfolio, snap)

        assert b1.batch_id == b2.batch_id
        assert [s.signal_id for s in b1.signals] == [s.signal_id for s in b2.signals]
        assert b1.batch_id == make_batch_id(
            portfolio.portfolio_id, snap.snapshot_id,
            tuple(s.signal_id for s in b1.signals))
        assert b1.signals[0].signal_id == make_signal_id(
            "EDGE-A", portfolio.portfolio_id, snap.snapshot_id,
            "BTCUSDT", SignalDirection.LONG)


class TestErrors:
    def test_non_active_edge_rejected(self):
        r = rule("RULE-1", "(GT RSI_14 70)")
        e = edge("EDGE-A", "RULE-1", status=EdgeStatus.VALIDATED)
        ereg = EdgeRegistry()
        ereg.register(e)
        rreg = RuleRegistry()
        rreg.register(r)
        akb = AKB()
        akb.add_node(NodeType.EDGE, e.edge_id, e)
        akb.add_node(NodeType.RULE, r.rule_id, r)
        portfolio = Portfolio(
            portfolio_id="PORT-X",
            policy_id="policy_v1",
            allocations=(PortfolioAllocation(e.edge_id, 1.0, SignalDirection.LONG),),
            status=PortfolioStatus.DRAFT,
        )
        engine = SignalEngine(ereg, rreg)
        with pytest.raises(SignalEngineError, match="ACTIVE"):
            engine.evaluate(portfolio, snapshot({"RSI_14": 75.0}))

    def test_missing_rule_rejected(self):
        e = edge("EDGE-A", "RULE-MISSING")
        engine, portfolio = build([e], [], [("EDGE-A", SignalDirection.LONG)])
        with pytest.raises(SignalEngineError, match="rule"):
            engine.evaluate(portfolio, snapshot({"RSI_14": 75.0}))

    def test_missing_feature_rejected(self):
        r = rule("RULE-1", "(GT RSI_14 70)")
        e = edge("EDGE-A", "RULE-1")
        engine, portfolio = build([e], [r], [("EDGE-A", SignalDirection.LONG)])
        with pytest.raises(SignalEngineError, match="feature"):
            engine.evaluate(portfolio, snapshot({"EMA_20": 100.0}))
