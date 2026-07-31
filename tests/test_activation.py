"""Tests for AlphaOS Activation Engine."""

from datetime import datetime, timedelta, timezone
import pytest

from shared.akb import AKB, NodeType
from shared.contracts import Edge, EdgeStatus, RelationshipType
from shared.evidence import Evidence, EvidenceStatus, evidence_id
from shared.registries import EdgeRegistry
from shared.activation import ActivationEngine, ActivationPolicy, ActivationRecord, DecayRecord


def make_evidence(candidate="CAND-1", exp="EXP-1", rule="RULE-1",
                  status=EvidenceStatus.SUPPORTS, metrics=None,
                  created_at=None) -> Evidence:
    m = metrics or {
        "sample": 300, "hit_rate": 0.60, "profit_factor": 1.50,
        "sharpe": 1.30, "rule_id": rule,
    }
    return Evidence(evidence_id=evidence_id(candidate, m), experiment_id=exp,
                    candidate_id=candidate, metrics=m, status=status,
                    created_at=created_at or datetime.now(timezone.utc))


def build_akb_with_edge(edge: Edge, ev: Evidence) -> AKB:
    akb = AKB()
    akb.add_node(NodeType.EDGE, edge.edge_id, edge)
    akb.add_node(NodeType.EVIDENCE, ev.evidence_id, ev)
    return akb


class TestActivation:
    def test_validated_edge_promotes_to_active(self):
        policy = ActivationPolicy("v1", 1.2, 1.4, 90, 300)
        reg = EdgeRegistry()
        ev = make_evidence()
        edge = Edge(edge_id="E1", rule_id="R1", experiment_id="EXP1",
                    supported_by=(ev.evidence_id,), status=EdgeStatus.VALIDATED)
        reg.register(edge)
        akb = build_akb_with_edge(edge, ev)
        engine = ActivationEngine(policy, reg, akb)

        record = engine.activate(edge.edge_id)

        assert isinstance(record, ActivationRecord)
        assert record.edge_id == edge.edge_id
        assert record.policy_id == policy.policy_id
        activated_edge = reg.get(edge.edge_id)
        assert activated_edge.status == EdgeStatus.ACTIVE
        assert len(reg.all_active()) == 1
        assert akb.get_node(NodeType.ACTIVATION_RECORD, record.activation_id).payload == record
        rels = akb.relationships_from(NodeType.EDGE, edge.edge_id,
                                      RelationshipType.ACTIVATED_BY)
        assert [(r.source_id, r.target_id) for r in rels] == [(edge.edge_id, record.activation_id)]

    def test_activation_fails_if_policy_not_met(self):
        policy = ActivationPolicy("v1", 1.2, 1.4, 90, 300)
        reg = EdgeRegistry()
        ev = make_evidence(metrics={"sharpe": 1.1})  # Fails policy
        edge = Edge(edge_id="E1", rule_id="R1", experiment_id="EXP1",
                    supported_by=(ev.evidence_id,), status=EdgeStatus.VALIDATED)
        reg.register(edge)
        akb = build_akb_with_edge(edge, ev)
        engine = ActivationEngine(policy, reg, akb)

        with pytest.raises(ValueError, match="sharpe"):
            engine.activate(edge.edge_id)
        assert reg.get(edge.edge_id).status == EdgeStatus.VALIDATED

    def test_non_validated_edge_cannot_be_activated(self):
        policy = ActivationPolicy("v1", 1.2, 1.4, 90, 300)
        reg = EdgeRegistry()
        ev = make_evidence()
        edge = Edge(edge_id="E1", rule_id="R1", experiment_id="EXP1",
                    supported_by=(ev.evidence_id,), status=EdgeStatus.DISCOVERED)
        reg.register(edge)
        akb = build_akb_with_edge(edge, ev)
        engine = ActivationEngine(policy, reg, akb)

        with pytest.raises(ValueError, match="VALIDATED"):
            engine.activate(edge.edge_id)


class TestDecay:
    def test_active_edge_decays_if_evidence_is_stale(self):
        policy = ActivationPolicy("v1", 1.2, 1.4, 90, 300)
        reg = EdgeRegistry()
        stale_date = datetime.now(timezone.utc) - timedelta(days=91)
        ev = make_evidence(created_at=stale_date)
        edge = Edge(edge_id="E1", rule_id="R1", experiment_id="EXP1",
                    supported_by=(ev.evidence_id,), status=EdgeStatus.ACTIVE)
        reg.register(edge)
        akb = build_akb_with_edge(edge, ev)
        engine = ActivationEngine(policy, reg, akb)

        decay_record = engine.decay(edge.edge_id)

        assert isinstance(decay_record, DecayRecord)
        decayed_edge = reg.get(edge.edge_id)
        assert decayed_edge.status == EdgeStatus.DECAYED
        assert len(reg.all_decayed()) == 1
        assert len(reg.all_active()) == 0
        assert akb.get_node(NodeType.ACTIVATION_RECORD, decay_record.decay_id).payload == decay_record
        rels = akb.relationships_from(NodeType.EDGE, edge.edge_id,
                                      RelationshipType.DECAYED_BY)
        assert [(r.source_id, r.target_id) for r in rels] == [(edge.edge_id, decay_record.decay_id)]

    def test_fresh_edge_does_not_decay(self):
        policy = ActivationPolicy("v1", 1.2, 1.4, 90, 300)
        reg = EdgeRegistry()
        ev = make_evidence()  # Fresh evidence
        edge = Edge(edge_id="E1", rule_id="R1", experiment_id="EXP1",
                    supported_by=(ev.evidence_id,), status=EdgeStatus.ACTIVE)
        reg.register(edge)
        akb = build_akb_with_edge(edge, ev)
        engine = ActivationEngine(policy, reg, akb)

        decay_record = engine.decay(edge.edge_id)
        assert decay_record is None
        assert reg.get(edge.edge_id).status == EdgeStatus.ACTIVE
