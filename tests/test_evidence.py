"""Tests for AlphaOS Evidence Model (ADR-008, spec evidence-model)."""

import pytest

from shared.evidence import (
    Evidence,
    EvidenceRegistry,
    EvidenceStatus,
    evidence_id,
    review,
)
from shared.registry import DuplicateActiveError, RegistryStatus


def make_evidence(cid="CAND-1", exp="EXP-1", metrics=None) -> Evidence:
    m = metrics or {"sample": 100, "hit_rate": 0.6}
    return Evidence(evidence_id=evidence_id(cid, m), experiment_id=exp,
                    candidate_id=cid, metrics=m)


class TestIdentity:
    def test_evidence_id_deterministic(self):
        m = {"sample": 100, "hit_rate": 0.6}
        assert evidence_id("CAND-1", m) == evidence_id("CAND-1", m)
        assert evidence_id("CAND-1", m).startswith("EVID-")

    def test_evidence_id_changes_with_metrics(self):
        m1 = {"sample": 100, "hit_rate": 0.6}
        m2 = {"sample": 100, "hit_rate": 0.7}
        assert evidence_id("CAND-1", m1) != evidence_id("CAND-1", m2)

    def test_evidence_id_key_order_insensitive(self):
        a = evidence_id("CAND-1", {"a": 1, "b": 2})
        b = evidence_id("CAND-1", {"b": 2, "a": 1})
        assert a == b


class TestRegistry:
    def test_register_get(self):
        reg = EvidenceRegistry()
        ev = make_evidence()
        reg.register(ev)
        assert reg.get(ev.evidence_id) == ev

    def test_duplicate_rejected(self):
        reg = EvidenceRegistry()
        ev = make_evidence()
        reg.register(ev)
        with pytest.raises(DuplicateActiveError):
            reg.register(ev)

    def test_traceability(self):
        reg = EvidenceRegistry()
        ev = make_evidence(cid="CAND-9", exp="EXP-7")
        reg.register(ev)
        got = reg.get(ev.evidence_id)
        assert got.candidate_id == "CAND-9"
        assert got.experiment_id == "EXP-7"

    def test_history(self):
        reg = EvidenceRegistry()
        ev = make_evidence()
        reg.register(ev)
        hist = reg.history(ev.evidence_id)
        assert len(hist) == 1
        assert hist[0].status == RegistryStatus.ACTIVE


class TestLifecycle:
    def test_generated_to_supports(self):
        reg = EvidenceRegistry()
        ev = make_evidence()
        entry = reg.register(ev)
        new = review(entry, EvidenceStatus.SUPPORTS, edge_id="EDGE-1")
        assert new.entity.status == EvidenceStatus.SUPPORTS
        assert new.entity.edge_id == "EDGE-1"
        # registry sees the advanced entry
        assert reg.get(ev.evidence_id).status == EvidenceStatus.SUPPORTS

    def test_generated_to_refutes(self):
        reg = EvidenceRegistry()
        ev = make_evidence()
        entry = reg.register(ev)
        new = review(entry, EvidenceStatus.REFUTES)
        assert new.entity.status == EvidenceStatus.REFUTES
        assert new.entity.edge_id is None

    def test_supports_requires_edge(self):
        reg = EvidenceRegistry()
        ev = make_evidence()
        entry = reg.register(ev)
        with pytest.raises(ValueError):
            review(entry, EvidenceStatus.SUPPORTS)  # no edge_id

    def test_refutes_cannot_carry_edge(self):
        reg = EvidenceRegistry()
        ev = make_evidence()
        entry = reg.register(ev)
        with pytest.raises(ValueError):
            review(entry, EvidenceStatus.REFUTES, edge_id="EDGE-1")

    def test_terminal_is_final(self):
        reg = EvidenceRegistry()
        ev = make_evidence()
        entry = reg.register(ev)
        new = review(entry, EvidenceStatus.REFUTES)
        with pytest.raises(ValueError):
            review(new, EvidenceStatus.SUPPORTS, edge_id="EDGE-1")

    def test_forward_only(self):
        reg = EvidenceRegistry()
        ev = make_evidence()
        entry = reg.register(ev)
        with pytest.raises(ValueError):
            review(entry, EvidenceStatus.GENERATED)  # same state not allowed

    def test_metrics_immutable_across_review(self):
        reg = EvidenceRegistry()
        ev = make_evidence(metrics={"sample": 300, "hit_rate": 0.6})
        entry = reg.register(ev)
        new = review(entry, EvidenceStatus.SUPPORTS, edge_id="EDGE-1")
        assert new.entity.metrics == {"sample": 300, "hit_rate": 0.6}


class TestQueries:
    def test_all_supporting_and_refuting(self):
        reg = EvidenceRegistry()
        e1 = make_evidence(cid="CAND-1")
        e2 = make_evidence(cid="CAND-2")
        e3 = make_evidence(cid="CAND-3")
        r1 = reg.register(e1)
        r2 = reg.register(e2)
        r3 = reg.register(e3)
        review(r1, EvidenceStatus.SUPPORTS, edge_id="EDGE-1")
        review(r2, EvidenceStatus.REFUTES)
        assert len(reg.all_supporting()) == 1
        assert len(reg.all_refuting()) == 1
        assert reg.all_supporting()[0].entity.candidate_id == "CAND-1"
        assert reg.all_refuting()[0].entity.candidate_id == "CAND-2"
