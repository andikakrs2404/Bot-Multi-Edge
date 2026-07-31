"""Tests for AlphaOS AKB Representation (ADR-009 graph contract)."""

import pytest

from shared.akb import (
    AKB,
    NodeType,
    link_edge_evidence,
    link_evidence_trace,
    register_production_decision,
)
from shared.contracts import Edge, EdgeStatus, Portfolio, ProductionDecision, RelationshipType
from shared.evidence import Evidence, EvidenceStatus, evidence_id


def ev(cid: str, exp: str, status=EvidenceStatus.SUPPORTS) -> Evidence:
    m = {"sample": 300, "hit_rate": 0.6}
    return Evidence(evidence_id=evidence_id(cid, m), experiment_id=exp,
                    candidate_id=cid, metrics=m, status=status)


def build_graph() -> tuple[AKB, Edge, Evidence, Evidence]:
    akb = AKB()
    akb.add_node(NodeType.DATASET, "DS-1", {"dataset_id": "DS-1"})
    akb.add_node(NodeType.EXPERIMENT, "EXP-1", {"dataset_id": "DS-1"})
    akb.add_node(NodeType.CANDIDATE, "CAND-1", {"experiment_id": "EXP-1"})
    e1 = ev("CAND-1", "EXP-1", EvidenceStatus.SUPPORTS)
    e2 = ev("CAND-2", "EXP-1", EvidenceStatus.SUPPORTS)
    edge = Edge(edge_id="EDGE-1", rule_id="RULE-1", experiment_id="EXP-1",
                supported_by=(e1.evidence_id, e2.evidence_id),
                status=EdgeStatus.ACTIVE)
    akb.add_node(NodeType.EVIDENCE, e1.evidence_id, e1)
    akb.add_node(NodeType.EVIDENCE, e2.evidence_id, e2)
    akb.add_node(NodeType.EDGE, edge.edge_id, edge)
    akb.add_relationship(RelationshipType.USES, NodeType.EXPERIMENT, "EXP-1",
                         NodeType.DATASET, "DS-1")
    link_evidence_trace(akb, e1, "CAND-1", "EXP-1")
    akb.add_node(NodeType.CANDIDATE, "CAND-2", {"experiment_id": "EXP-1"})
    link_evidence_trace(akb, e2, "CAND-2", "EXP-1")
    link_edge_evidence(akb, edge, e1)
    link_edge_evidence(akb, edge, e2)
    return akb, edge, e1, e2


class TestGraphBasics:
    def test_node_duplicate_rejected(self):
        akb = AKB()
        akb.add_node(NodeType.DATASET, "DS-1", {})
        with pytest.raises(ValueError):
            akb.add_node(NodeType.DATASET, "DS-1", {})

    def test_relationship_requires_existing_nodes(self):
        akb = AKB()
        akb.add_node(NodeType.DATASET, "DS-1", {})
        with pytest.raises(KeyError):
            akb.add_relationship(RelationshipType.USES, NodeType.EXPERIMENT, "EXP-1",
                                 NodeType.DATASET, "DS-1")

    def test_relationships_from_to(self):
        akb = AKB()
        akb.add_node(NodeType.EXPERIMENT, "EXP-1", {})
        akb.add_node(NodeType.DATASET, "DS-1", {})
        akb.add_relationship(RelationshipType.USES, NodeType.EXPERIMENT, "EXP-1",
                             NodeType.DATASET, "DS-1")
        assert len(akb.relationships_from(NodeType.EXPERIMENT, "EXP-1")) == 1
        assert len(akb.relationships_to(NodeType.DATASET, "DS-1")) == 1

    def test_duplicate_relationship_deduped(self):
        akb = AKB()
        akb.add_node(NodeType.EXPERIMENT, "EXP-1", {})
        akb.add_node(NodeType.DATASET, "DS-1", {})
        for _ in range(2):
            akb.add_relationship(RelationshipType.USES, NodeType.EXPERIMENT, "EXP-1",
                                 NodeType.DATASET, "DS-1")
        assert len(akb.relationships_from(NodeType.EXPERIMENT, "EXP-1")) == 1


class TestQueryGuarantees:
    def test_edge_evidence_is_one_to_many(self):
        akb, edge, e1, e2 = build_graph()
        got = akb.evidence_for_edge(edge.edge_id)
        assert {n.node_id for n in got} == {e1.evidence_id, e2.evidence_id}

    def test_trace_evidence(self):
        akb, _, e1, _ = build_graph()
        tr = akb.trace_evidence(e1.evidence_id)
        assert tr["evidence"].node_id == e1.evidence_id
        assert tr["candidate"].node_id == "CAND-1"
        assert tr["experiment"].node_id == "EXP-1"

    def test_trace_edge_to_datasets(self):
        akb, edge, _, _ = build_graph()
        ds = akb.trace_edge_to_datasets(edge.edge_id)
        assert [n.node_id for n in ds] == ["DS-1"]

    def test_production_decision_trace(self):
        akb, edge, _, _ = build_graph()
        portfolio = Portfolio(portfolio_id="P-1", allocations=((edge.edge_id, 1.0),))
        akb.add_node(NodeType.PORTFOLIO, portfolio.portfolio_id, portfolio)
        akb.add_relationship(RelationshipType.ALLOCATED_TO, NodeType.EDGE, edge.edge_id,
                             NodeType.PORTFOLIO, portfolio.portfolio_id)
        decision = ProductionDecision(decision_id="D-1", portfolio_id="P-1",
                                      triggered_edges=(edge.edge_id,),
                                      decision="BUY", confidence=0.8)
        register_production_decision(akb, decision)
        akb.add_relationship(RelationshipType.DRIVES, NodeType.PORTFOLIO,
                             portfolio.portfolio_id, NodeType.PRODUCTION_DECISION,
                             decision.decision_id)
        tr = akb.trace_production_decision(decision.decision_id)
        assert tr["decision"].node_id == "D-1"
        assert [n.node_id for n in tr["portfolios"]] == ["P-1"]
        assert [n.node_id for n in tr["edges"]] == [edge.edge_id]
        assert len(tr["evidence"]) == 2
        assert [n.node_id for n in tr["datasets"]] == ["DS-1"]

    def test_given_rule_find_experiments_via_relationships(self):
        akb = AKB()
        akb.add_node(NodeType.RULE, "RULE-1", {})
        akb.add_node(NodeType.EXPERIMENT, "EXP-1", {})
        akb.add_relationship(RelationshipType.USES, NodeType.EXPERIMENT, "EXP-1",
                             NodeType.RULE, "RULE-1")
        assert [n.node_id for n in akb.experiments_for_rule("RULE-1")] == ["EXP-1"]


class TestIntegrity:
    def test_active_edge_requires_supports_evidence(self):
        akb = AKB()
        edge = Edge(edge_id="EDGE-1", rule_id="R", experiment_id="E",
                    status=EdgeStatus.ACTIVE)
        akb.add_node(NodeType.EDGE, edge.edge_id, edge)
        with pytest.raises(ValueError):
            akb.validate_active_edge(edge.edge_id)

    def test_active_edge_rejects_refuting_evidence(self):
        akb = AKB()
        bad = ev("CAND-1", "EXP-1", EvidenceStatus.REFUTES)
        edge = Edge(edge_id="EDGE-1", rule_id="R", experiment_id="E",
                    supported_by=(bad.evidence_id,), status=EdgeStatus.ACTIVE)
        akb.add_node(NodeType.EDGE, edge.edge_id, edge)
        akb.add_node(NodeType.EVIDENCE, bad.evidence_id, bad)
        link_edge_evidence(akb, edge, bad)
        with pytest.raises(ValueError):
            akb.validate_active_edge(edge.edge_id)

    def test_active_edge_accepts_supporting_evidence(self):
        akb, edge, _, _ = build_graph()
        akb.validate_active_edge(edge.edge_id)

    def test_production_decision_requires_triggered_edges(self):
        akb = AKB()
        d = ProductionDecision(decision_id="D", portfolio_id="P",
                               triggered_edges=(), decision="HOLD", confidence=0.1)
        with pytest.raises(ValueError):
            register_production_decision(akb, d)

    def test_production_decision_rejects_non_active_edge(self):
        akb = AKB()
        edge = Edge(edge_id="EDGE-1", rule_id="R", experiment_id="E",
                    status=EdgeStatus.DISCOVERED)
        akb.add_node(NodeType.EDGE, edge.edge_id, edge)
        d = ProductionDecision(decision_id="D", portfolio_id="P",
                               triggered_edges=(edge.edge_id,),
                               decision="BUY", confidence=0.9)
        with pytest.raises(ValueError):
            register_production_decision(akb, d)


class TestContractChanges:
    def test_edge_supported_by_is_one_to_many(self):
        e = Edge(edge_id="EDGE-1", rule_id="R", experiment_id="EXP",
                 supported_by=("EVID-1", "EVID-2"))
        assert e.supported_by == ("EVID-1", "EVID-2")

    def test_references_relationship_exists(self):
        assert RelationshipType.REFERENCES.value == "references"
        assert RelationshipType.DERIVED_FROM.value == "derived_from"
