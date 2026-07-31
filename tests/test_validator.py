"""Tests for AlphaOS Validator Engine (Evidence → Edge promotion)."""

import pytest

from shared.akb import AKB, NodeType
from shared.contracts import EdgeStatus, RelationshipType
from shared.evidence import Evidence, EvidenceStatus, evidence_id
from shared.registries import EdgeRegistry
from shared.registry import DuplicateActiveError
from shared.validator import ValidationPolicy, ValidatorEngine, edge_id


def make_evidence(candidate="CAND-1", exp="EXP-1", rule="RULE-1",
                  status=EvidenceStatus.SUPPORTS, metrics=None) -> Evidence:
    m = metrics or {
        "sample": 300,
        "hit_rate": 0.60,
        "profit_factor": 1.50,
        "sharpe": 1.30,
        "rule_id": rule,
    }
    return Evidence(evidence_id=evidence_id(candidate, m), experiment_id=exp,
                    candidate_id=candidate, metrics=m, status=status)


def build_akb(ev: Evidence) -> AKB:
    akb = AKB()
    akb.add_node(NodeType.DATASET, "DS-1", {"dataset_id": "DS-1"})
    akb.add_node(NodeType.EXPERIMENT, ev.experiment_id, {"dataset_id": "DS-1"})
    akb.add_node(NodeType.CANDIDATE, ev.candidate_id,
                 {"experiment_id": ev.experiment_id})
    akb.add_node(NodeType.EVIDENCE, ev.evidence_id, ev)
    akb.add_relationship(RelationshipType.USES, NodeType.EXPERIMENT,
                         ev.experiment_id, NodeType.DATASET, "DS-1")
    akb.add_relationship(RelationshipType.REFERENCES, NodeType.EVIDENCE,
                         ev.evidence_id, NodeType.CANDIDATE, ev.candidate_id)
    akb.add_relationship(RelationshipType.REFERENCES, NodeType.EVIDENCE,
                         ev.evidence_id, NodeType.EXPERIMENT, ev.experiment_id)
    return akb


class TestPolicy:
    def test_policy_id_deterministic(self):
        p1 = ValidationPolicy("validator_policy_v1", 300, 0.55, 1.3, 1.2)
        p2 = ValidationPolicy("validator_policy_v1", 300, 0.55, 1.3, 1.2)
        assert p1 == p2

    def test_edge_id_deterministic(self):
        assert edge_id("RULE-1", ("EVID-1", "EVID-2")) == edge_id(
            "RULE-1", ("EVID-2", "EVID-1")
        )
        assert edge_id("RULE-1", ("EVID-1",)).startswith("EDGE-")


class TestPromotion:
    def test_supports_evidence_promotes_to_validated_edge(self):
        ev = make_evidence()
        akb = build_akb(ev)
        reg = EdgeRegistry()
        engine = ValidatorEngine(ValidationPolicy("v1", 300, 0.55, 1.3, 1.2), reg, akb)

        edge = engine.promote("RULE-1", [ev])

        assert edge.status == EdgeStatus.VALIDATED
        assert edge.rule_id == "RULE-1"
        assert edge.experiment_id == "EXP-1"
        assert edge.supported_by == (ev.evidence_id,)
        assert edge.policy_id == "v1"
        assert reg.get(edge.edge_id) == edge
        assert len(reg.all_validated()) == 1
        assert len(reg.all_active()) == 0

    @pytest.mark.parametrize("status", [
        EvidenceStatus.GENERATED,
        EvidenceStatus.REVIEWED,
        EvidenceStatus.REFUTES,
    ])
    def test_non_supports_evidence_rejected(self, status):
        ev = make_evidence(status=status)
        engine = ValidatorEngine(ValidationPolicy("v1", 300, 0.55, 1.3, 1.2), EdgeRegistry(), AKB())
        with pytest.raises(ValueError, match="SUPPORTS"):
            engine.promote("RULE-1", [ev])

    @pytest.mark.parametrize("metric,value", [
        ("sample", 299),
        ("hit_rate", 0.54),
        ("profit_factor", 1.29),
        ("sharpe", 1.19),
    ])
    def test_policy_thresholds_enforced(self, metric, value):
        metrics = {
            "sample": 300,
            "hit_rate": 0.60,
            "profit_factor": 1.50,
            "sharpe": 1.30,
            "rule_id": "RULE-1",
        }
        metrics[metric] = value
        ev = make_evidence(metrics=metrics)
        engine = ValidatorEngine(ValidationPolicy("v1", 300, 0.55, 1.3, 1.2), EdgeRegistry(), AKB())
        with pytest.raises(ValueError, match=metric):
            engine.promote("RULE-1", [ev])

    def test_multi_evidence_support(self):
        e1 = make_evidence(candidate="CAND-1")
        e2 = make_evidence(candidate="CAND-1", metrics={
            "sample": 400, "hit_rate": 0.62, "profit_factor": 1.7,
            "sharpe": 1.4, "rule_id": "RULE-1",
        })
        akb = build_akb(e1)
        akb.add_node(NodeType.EVIDENCE, e2.evidence_id, e2)
        akb.add_relationship(RelationshipType.REFERENCES, NodeType.EVIDENCE,
                             e2.evidence_id, NodeType.CANDIDATE, e2.candidate_id)
        akb.add_relationship(RelationshipType.REFERENCES, NodeType.EVIDENCE,
                             e2.evidence_id, NodeType.EXPERIMENT, e2.experiment_id)
        engine = ValidatorEngine(ValidationPolicy("v1", 300, 0.55, 1.3, 1.2), EdgeRegistry(), akb)

        edge = engine.promote("RULE-1", [e2, e1])

        assert edge.supported_by == tuple(sorted([e1.evidence_id, e2.evidence_id]))
        assert len(akb.evidence_for_edge(edge.edge_id)) == 2

    def test_duplicate_edge_rejected(self):
        ev = make_evidence()
        akb = build_akb(ev)
        reg = EdgeRegistry()
        engine = ValidatorEngine(ValidationPolicy("v1", 300, 0.55, 1.3, 1.2), reg, akb)
        engine.promote("RULE-1", [ev])
        with pytest.raises(DuplicateActiveError):
            engine.promote("RULE-1", [ev])

    def test_mixed_experiment_evidence_rejected(self):
        e1 = make_evidence(exp="EXP-1")
        e2 = make_evidence(exp="EXP-2")
        engine = ValidatorEngine(ValidationPolicy("v1", 300, 0.55, 1.3, 1.2), EdgeRegistry(), AKB())
        with pytest.raises(ValueError, match="same experiment"):
            engine.promote("RULE-1", [e1, e2])

    def test_no_active_edge_created(self):
        ev = make_evidence()
        engine = ValidatorEngine(ValidationPolicy("v1", 300, 0.55, 1.3, 1.2), EdgeRegistry(), build_akb(ev))
        edge = engine.promote("RULE-1", [ev])
        assert edge.status is EdgeStatus.VALIDATED
        assert edge.status is not EdgeStatus.ACTIVE


class TestRegistryQueries:
    def test_edge_registry_queries(self):
        ev = make_evidence()
        reg = EdgeRegistry()
        engine = ValidatorEngine(ValidationPolicy("v1", 300, 0.55, 1.3, 1.2), reg, build_akb(ev))
        edge = engine.promote("RULE-1", [ev])
        assert [e.entity.edge_id for e in reg.all_validated()] == [edge.edge_id]
        assert reg.all_active() == []
        assert reg.all_decayed() == []

    def test_edge_lifecycle_transition_queries(self):
        ev = make_evidence()
        reg = EdgeRegistry()
        engine = ValidatorEngine(ValidationPolicy("v1", 300, 0.55, 1.3, 1.2), reg, build_akb(ev))
        edge = engine.promote("RULE-1", [ev])
        entry = reg.latest_entry(edge.edge_id)
        active = reg.set_status(entry, EdgeStatus.ACTIVE)
        assert [e.entity.edge_id for e in reg.all_active()] == [edge.edge_id]
        decayed = reg.set_status(active, EdgeStatus.DECAYED)
        assert [e.entity.edge_id for e in reg.all_decayed()] == [edge.edge_id]
        assert reg.all_active() == []


class TestTraceability:
    def test_edge_trace_to_dataset_after_promotion(self):
        ev = make_evidence()
        akb = build_akb(ev)
        engine = ValidatorEngine(ValidationPolicy("v1", 300, 0.55, 1.3, 1.2), EdgeRegistry(), akb)
        edge = engine.promote("RULE-1", [ev])
        assert [n.node_id for n in akb.evidence_for_edge(edge.edge_id)] == [ev.evidence_id]
        trace = akb.trace_evidence(ev.evidence_id)
        assert trace["candidate"].node_id == ev.candidate_id
        assert trace["experiment"].node_id == ev.experiment_id
        assert [n.node_id for n in akb.trace_edge_to_datasets(edge.edge_id)] == ["DS-1"]

    def test_promotion_adds_supported_by_relationship(self):
        ev = make_evidence()
        akb = build_akb(ev)
        engine = ValidatorEngine(ValidationPolicy("v1", 300, 0.55, 1.3, 1.2), EdgeRegistry(), akb)
        edge = engine.promote("RULE-1", [ev])
        rels = akb.relationships_from(NodeType.EDGE, edge.edge_id, RelationshipType.SUPPORTED_BY)
        assert [(r.source_id, r.target_id) for r in rels] == [(edge.edge_id, ev.evidence_id)]
