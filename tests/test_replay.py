"""Tests for AlphaOS ReplayEngine (read-only ledger views)."""

from datetime import datetime, timezone

import pytest

from shared.contracts import ProductionDecision
from shared.ledger import ProductionLedger
from shared.replay import ReplayEngine


def decision(decision_id, portfolio_id="PORT-1", decision="BUY",
             triggered_edges=("EDGE-A",), confidence=0.8,
             ts=datetime(2026, 8, 1, 9, 0, 0, tzinfo=timezone.utc)):
    return ProductionDecision(
        decision_id=decision_id,
        portfolio_id=portfolio_id,
        triggered_edges=triggered_edges,
        decision=decision,
        confidence=confidence,
        ts=ts,
    )


def ledger_with(decisions: list[ProductionDecision]) -> ProductionLedger:
    ledger = ProductionLedger()
    for d in decisions:
        ledger.append(d)
    return ledger


class TestDecisionTimeline:
    def test_chronological_order(self):
        ledger = ledger_with([
            decision("D-1", decision="HOLD"),
            decision("D-2", decision="BUY"),
            decision("D-3", decision="SELL"),
        ])
        engine = ReplayEngine(ledger)
        result = engine.replay()

        tl = result.decision_timeline()
        assert [e.decision_id for e in tl] == ["D-1", "D-2", "D-3"]
        assert tl[1].decision == "BUY"

    def test_filter_by_portfolio(self):
        ledger = ledger_with([
            decision("D-1", portfolio_id="PORT-1"),
            decision("D-2", portfolio_id="PORT-2"),
            decision("D-3", portfolio_id="PORT-1"),
        ])
        result = ReplayEngine(ledger).replay()

        tl = result.decision_timeline(portfolio_id="PORT-1")
        assert [e.decision_id for e in tl] == ["D-1", "D-3"]


class TestPortfolioTimeline:
    def test_groups_by_portfolio(self):
        ledger = ledger_with([
            decision("D-1", portfolio_id="PORT-1"),
            decision("D-2", portfolio_id="PORT-2"),
            decision("D-3", portfolio_id="PORT-1"),
        ])
        result = ReplayEngine(ledger).replay()

        pt = result.portfolio_timeline()
        by_port = {p.portfolio_id: [e.decision_id for e in p.entries]
                   for p in pt}
        assert by_port == {"PORT-1": ["D-1", "D-3"], "PORT-2": ["D-2"]}


class TestEdgeTimeline:
    def test_aggregates_edges_from_decisions(self):
        ledger = ledger_with([
            decision("D-1", triggered_edges=("EDGE-A",)),
            decision("D-2", triggered_edges=("EDGE-A", "EDGE-B")),
            decision("D-3", triggered_edges=("EDGE-B",)),
        ])
        result = ReplayEngine(ledger).replay()

        et = result.edge_timeline()
        by_edge = {e.edge_id: [ev.decision_id for ev in e.events]
                   for e in et}
        assert by_edge == {"EDGE-A": ["D-1", "D-2"],
                           "EDGE-B": ["D-2", "D-3"]}

    def test_filter_by_edge(self):
        ledger = ledger_with([
            decision("D-1", triggered_edges=("EDGE-A",)),
            decision("D-2", triggered_edges=("EDGE-A", "EDGE-B")),
        ])
        result = ReplayEngine(ledger).replay()

        et = result.edge_timeline(edge_id="EDGE-B")
        assert [e.decision_id for e in et] == ["D-2"]


class TestDeterminismAndReadOnly:
    def test_replay_twice_identical(self):
        ledger = ledger_with([
            decision("D-1", decision="HOLD"),
            decision("D-2", decision="BUY"),
        ])
        engine = ReplayEngine(ledger)

        r1 = engine.replay()
        r2 = engine.replay()

        assert r1.decision_timeline() == r2.decision_timeline()
        assert r1.portfolio_timeline() == r2.portfolio_timeline()
        assert r1.edge_timeline() == r2.edge_timeline()

    def test_read_only_no_mutation(self):
        ledger = ledger_with([
            decision("D-1", decision="BUY"),
            decision("D-2", decision="SELL"),
        ])
        before = ledger.all()
        ReplayEngine(ledger).replay()

        assert ledger.all() == before
        assert [e.decision_id for e in ledger.all()] == ["D-1", "D-2"]

    def test_empty_ledger(self):
        result = ReplayEngine(ProductionLedger()).replay()
        assert result.decision_timeline() == ()
        assert result.portfolio_timeline() == ()
        assert result.edge_timeline() == ()
