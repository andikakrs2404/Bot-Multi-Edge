"""Tests for AlphaOS ProductionLedger (Decision → Recorded Fact)."""

from datetime import datetime, timezone

import pytest

from shared.contracts import ProductionDecision
from shared.ledger import LedgerEntry, ProductionLedger


def decision(decision_id="D-1", portfolio_id="PORT-1", decision="BUY",
             confidence=0.8) -> ProductionDecision:
    return ProductionDecision(
        decision_id=decision_id,
        portfolio_id=portfolio_id,
        triggered_edges=("EDGE-A",),
        decision=decision,
        confidence=confidence,
    )


class TestAppend:
    def test_append_and_retrieve(self):
        ledger = ProductionLedger()
        entry = ledger.append(decision())

        assert isinstance(entry, LedgerEntry)
        assert entry.decision_id == "D-1"
        assert entry.portfolio_id == "PORT-1"
        assert entry.decision.decision == "BUY"
        assert entry.recorded_at.tzinfo is not None
        assert ledger.by_decision("D-1") == entry

    def test_entry_id_deterministic(self):
        l1, l2 = ProductionLedger(), ProductionLedger()
        e1 = l1.append(decision())
        e2 = l2.append(decision())

        assert e1.entry_id == e2.entry_id

    def test_duplicate_decision_rejected(self):
        ledger = ProductionLedger()
        ledger.append(decision())
        with pytest.raises(ValueError, match="duplicate"):
            ledger.append(decision())

    def test_by_decision_missing_raises(self):
        ledger = ProductionLedger()
        with pytest.raises(KeyError):
            ledger.by_decision("NOPE")


class TestQueries:
    def test_by_portfolio_filters(self):
        ledger = ProductionLedger()
        ledger.append(decision(decision_id="D-1", portfolio_id="PORT-1"))
        ledger.append(decision(decision_id="D-2", portfolio_id="PORT-2"))
        ledger.append(decision(decision_id="D-3", portfolio_id="PORT-1"))

        got = ledger.by_portfolio("PORT-1")
        assert [e.decision_id for e in got] == ["D-1", "D-3"]

    def test_all_append_order(self):
        ledger = ProductionLedger()
        ledger.append(decision(decision_id="D-1"))
        ledger.append(decision(decision_id="D-2"))
        ledger.append(decision(decision_id="D-3"))

        got = ledger.all()
        assert [e.decision_id for e in got] == ["D-1", "D-2", "D-3"]
