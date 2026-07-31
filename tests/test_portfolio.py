"""Tests for AlphaOS Portfolio (ACTIVE Edge selection only)."""

import pytest

from shared.akb import AKB, NodeType
from shared.contracts import Edge, EdgeStatus, PortfolioStatus, RelationshipType
from shared.portfolio import (
    Portfolio,
    PortfolioBuilder,
    PortfolioError,
    PortfolioPolicy,
    WeightingMethod,
    portfolio_id,
)
from shared.registries import EdgeRegistry, PortfolioRegistry


def edge(edge_id: str, status: EdgeStatus = EdgeStatus.ACTIVE) -> Edge:
    return Edge(edge_id=edge_id, rule_id=f"RULE-{edge_id}", experiment_id="EXP-1",
                supported_by=(f"EVID-{edge_id}",), status=status)


def edge_registry(*edges: Edge) -> EdgeRegistry:
    reg = EdgeRegistry()
    for e in edges:
        reg.register(e)
    return reg


def akb_with_edges(*edges: Edge) -> AKB:
    akb = AKB()
    for e in edges:
        akb.add_node(NodeType.EDGE, e.edge_id, e)
    return akb


class TestIdentity:
    def test_portfolio_id_deterministic_and_order_insensitive(self):
        assert portfolio_id("policy_v1", ("EDGE-C", "EDGE-A", "EDGE-B")) == portfolio_id(
            "policy_v1", ("EDGE-A", "EDGE-B", "EDGE-C")
        )
        assert portfolio_id("policy_v1", ("EDGE-A",)).startswith("PORT-")

    def test_membership_change_changes_id(self):
        a = portfolio_id("policy_v1", ("EDGE-A", "EDGE-B"))
        b = portfolio_id("policy_v1", ("EDGE-A", "EDGE-B", "EDGE-C"))
        assert a != b


class TestBuilder:
    def test_create_portfolio_from_active_edges(self):
        e1, e2 = edge("EDGE-B"), edge("EDGE-A")
        policy = PortfolioPolicy("policy_v1", max_edges=5,
                                 weighting_method=WeightingMethod.EQUAL_WEIGHT)
        akb = akb_with_edges(e1, e2)
        reg = edge_registry(e1, e2)
        preg = PortfolioRegistry()
        builder = PortfolioBuilder(policy, reg, preg, akb)

        p = builder.create(["EDGE-B", "EDGE-A"])

        assert isinstance(p, Portfolio)
        assert p.policy_id == "policy_v1"
        assert p.edge_ids == ("EDGE-A", "EDGE-B")
        assert p.status == PortfolioStatus.DRAFT
        assert p.allocations == (("EDGE-A", 0.5), ("EDGE-B", 0.5))
        assert preg.get(p.portfolio_id) == p

    @pytest.mark.parametrize("status", [
        EdgeStatus.VALIDATED,
        EdgeStatus.DECAYED,
        EdgeStatus.RETIRED,
        EdgeStatus.DISCOVERED,
    ])
    def test_reject_non_active_edges(self, status):
        e = edge("EDGE-A", status)
        policy = PortfolioPolicy("policy_v1", max_edges=5,
                                 weighting_method=WeightingMethod.EQUAL_WEIGHT)
        builder = PortfolioBuilder(policy, edge_registry(e), PortfolioRegistry(), akb_with_edges(e))
        with pytest.raises(PortfolioError, match="ACTIVE"):
            builder.create(["EDGE-A"])

    def test_reject_duplicate_edge(self):
        e = edge("EDGE-A")
        policy = PortfolioPolicy("policy_v1", max_edges=5,
                                 weighting_method=WeightingMethod.EQUAL_WEIGHT)
        builder = PortfolioBuilder(policy, edge_registry(e), PortfolioRegistry(), akb_with_edges(e))
        with pytest.raises(PortfolioError, match="duplicate"):
            builder.create(["EDGE-A", "EDGE-A"])

    def test_reject_more_than_max_edges(self):
        edges = [edge("EDGE-A"), edge("EDGE-B")]
        policy = PortfolioPolicy("policy_v1", max_edges=1,
                                 weighting_method=WeightingMethod.EQUAL_WEIGHT)
        builder = PortfolioBuilder(policy, edge_registry(*edges), PortfolioRegistry(), akb_with_edges(*edges))
        with pytest.raises(PortfolioError, match="max_edges"):
            builder.create(["EDGE-A", "EDGE-B"])

    def test_equal_weights_sum_to_one(self):
        edges = [edge("EDGE-A"), edge("EDGE-B"), edge("EDGE-C")]
        policy = PortfolioPolicy("policy_v1", max_edges=5,
                                 weighting_method=WeightingMethod.EQUAL_WEIGHT)
        p = PortfolioBuilder(policy, edge_registry(*edges), PortfolioRegistry(), akb_with_edges(*edges)).create(
            ["EDGE-C", "EDGE-A", "EDGE-B"]
        )
        assert round(sum(w for _, w in p.allocations), 10) == 1.0
        assert all(w == pytest.approx(1 / 3) for _, w in p.allocations)

    def test_empty_portfolio_rejected(self):
        policy = PortfolioPolicy("policy_v1", max_edges=5,
                                 weighting_method=WeightingMethod.EQUAL_WEIGHT)
        builder = PortfolioBuilder(policy, EdgeRegistry(), PortfolioRegistry(), AKB())
        with pytest.raises(PortfolioError, match="at least one"):
            builder.create([])


class TestRegistry:
    def test_portfolio_registry_lookup_and_queries(self):
        e = edge("EDGE-A")
        policy = PortfolioPolicy("policy_v1", max_edges=5,
                                 weighting_method=WeightingMethod.EQUAL_WEIGHT)
        preg = PortfolioRegistry()
        p = PortfolioBuilder(policy, edge_registry(e), preg, akb_with_edges(e)).create(["EDGE-A"])
        assert preg.get(p.portfolio_id) == p
        assert [x.entity.portfolio_id for x in preg.all_draft()] == [p.portfolio_id]
        assert preg.all_live() == []


class TestAKB:
    def test_allocated_to_relationship_created(self):
        e = edge("EDGE-A")
        policy = PortfolioPolicy("policy_v1", max_edges=5,
                                 weighting_method=WeightingMethod.EQUAL_WEIGHT)
        akb = akb_with_edges(e)
        p = PortfolioBuilder(policy, edge_registry(e), PortfolioRegistry(), akb).create(["EDGE-A"])
        assert akb.get_node(NodeType.PORTFOLIO, p.portfolio_id).payload == p
        rels = akb.relationships_from(NodeType.EDGE, "EDGE-A", RelationshipType.ALLOCATED_TO)
        assert [(r.source_id, r.target_id) for r in rels] == [("EDGE-A", p.portfolio_id)]

    def test_no_production_decision_created(self):
        e = edge("EDGE-A")
        policy = PortfolioPolicy("policy_v1", max_edges=5,
                                 weighting_method=WeightingMethod.EQUAL_WEIGHT)
        akb = akb_with_edges(e)
        PortfolioBuilder(policy, edge_registry(e), PortfolioRegistry(), akb).create(["EDGE-A"])
        assert not [n for n in akb.nodes if n[0] == NodeType.PRODUCTION_DECISION]
