"""Tests for AlphaOS Portfolio (ACTIVE Edge selection only)."""

import pytest

from shared.akb import AKB, NodeType
from shared.contracts import (
    Edge,
    EdgeStatus,
    PortfolioAllocation,
    PortfolioStatus,
    RelationshipType,
    SignalDirection,
)
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
    return Edge(
        edge_id=edge_id,
        rule_id=f"RULE-{edge_id}",
        experiment_id="EXP-1",
        supported_by=(f"EVID-{edge_id}",),
        status=status,
    )


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
        p_id_1 = portfolio_id(
            "policy_v1", (("EDGE-C", SignalDirection.LONG), ("EDGE-A", SignalDirection.LONG), ("EDGE-B", SignalDirection.LONG))
        )
        p_id_2 = portfolio_id(
            "policy_v1", (("EDGE-A", SignalDirection.LONG), ("EDGE-B", SignalDirection.LONG), ("EDGE-C", SignalDirection.LONG))
        )
        assert p_id_1 == p_id_2
        assert p_id_1.startswith("PORT-")

    def test_membership_change_changes_id(self):
        a = portfolio_id("policy_v1", (("EDGE-A", SignalDirection.LONG), ("EDGE-B", SignalDirection.LONG)))
        b = portfolio_id("policy_v1", (("EDGE-A", SignalDirection.LONG), ("EDGE-B", SignalDirection.LONG), ("EDGE-C", SignalDirection.LONG)))
        assert a != b


class TestBuilder:
    def test_create_portfolio_from_active_edges(self):
        e1, e2 = edge("EDGE-B"), edge("EDGE-A")
        policy = PortfolioPolicy(
            "policy_v1", max_edges=5, weighting_method=WeightingMethod.EQUAL_WEIGHT
        )
        akb = akb_with_edges(e1, e2)
        reg = edge_registry(e1, e2)
        preg = PortfolioRegistry()
        builder = PortfolioBuilder(policy, reg, preg, akb)

        p = builder.create(
            [
                ("EDGE-B", SignalDirection.LONG),
                ("EDGE-A", SignalDirection.SHORT),
            ]
        )

        assert isinstance(p, Portfolio)
        assert p.policy_id == "policy_v1"
        assert p.status == PortfolioStatus.DRAFT
        # Check allocations (sorted by edge_id)
        assert p.allocations[0].edge_id == "EDGE-A"
        assert p.allocations[0].weight == 0.5
        assert p.allocations[0].direction == SignalDirection.SHORT
        assert p.allocations[1].edge_id == "EDGE-B"
        assert p.allocations[1].weight == 0.5
        assert p.allocations[1].direction == SignalDirection.LONG
        assert preg.get(p.portfolio_id) == p

    @pytest.mark.parametrize(
        "status",
        [
            EdgeStatus.VALIDATED,
            EdgeStatus.DECAYED,
            EdgeStatus.RETIRED,
            EdgeStatus.DISCOVERED,
        ],
    )
    def test_reject_non_active_edges(self, status):
        e = edge("EDGE-A", status)
        policy = PortfolioPolicy(
            "policy_v1", max_edges=5, weighting_method=WeightingMethod.EQUAL_WEIGHT
        )
        builder = PortfolioBuilder(
            policy, edge_registry(e), PortfolioRegistry(), akb_with_edges(e)
        )
        with pytest.raises(PortfolioError, match="ACTIVE"):
            builder.create([("EDGE-A", SignalDirection.LONG)])

    def test_reject_duplicate_edge(self):
        e = edge("EDGE-A")
        policy = PortfolioPolicy(
            "policy_v1", max_edges=5, weighting_method=WeightingMethod.EQUAL_WEIGHT
        )
        builder = PortfolioBuilder(
            policy, edge_registry(e), PortfolioRegistry(), akb_with_edges(e)
        )
        with pytest.raises(PortfolioError, match="duplicate"):
            builder.create([("EDGE-A", SignalDirection.LONG), ("EDGE-A", SignalDirection.SHORT)])

    def test_reject_more_than_max_edges(self):
        edges = [edge("EDGE-A"), edge("EDGE-B")]
        policy = PortfolioPolicy(
            "policy_v1", max_edges=1, weighting_method=WeightingMethod.EQUAL_WEIGHT
        )
        builder = PortfolioBuilder(
            policy, edge_registry(*edges), PortfolioRegistry(), akb_with_edges(*edges)
        )
        with pytest.raises(PortfolioError, match="max_edges"):
            builder.create([("EDGE-A", SignalDirection.LONG), ("EDGE-B", SignalDirection.LONG)])

    def test_equal_weights_sum_to_one(self):
        edges = [edge("EDGE-A"), edge("EDGE-B"), edge("EDGE-C")]
        policy = PortfolioPolicy(
            "policy_v1", max_edges=5, weighting_method=WeightingMethod.EQUAL_WEIGHT
        )
        p = PortfolioBuilder(
            policy, edge_registry(*edges), PortfolioRegistry(), akb_with_edges(*edges)
        ).create([("EDGE-C", SignalDirection.LONG), ("EDGE-A", SignalDirection.LONG), ("EDGE-B", SignalDirection.LONG)])
        assert round(sum(a.weight for a in p.allocations), 10) == 1.0
        assert all(a.weight == pytest.approx(1 / 3) for a in p.allocations)

    def test_empty_portfolio_rejected(self):
        policy = PortfolioPolicy(
            "policy_v1", max_edges=5, weighting_method=WeightingMethod.EQUAL_WEIGHT
        )
        builder = PortfolioBuilder(policy, EdgeRegistry(), PortfolioRegistry(), AKB())
        with pytest.raises(PortfolioError, match="at least one"):
            builder.create([])


class TestRegistry:
    def test_portfolio_registry_lookup_and_queries(self):
        e = edge("EDGE-A")
        policy = PortfolioPolicy(
            "policy_v1", max_edges=5, weighting_method=WeightingMethod.EQUAL_WEIGHT
        )
        preg = PortfolioRegistry()
        p = PortfolioBuilder(policy, edge_registry(e), preg, akb_with_edges(e)).create(
            [("EDGE-A", SignalDirection.LONG)]
        )
        assert preg.get(p.portfolio_id) == p
        assert [x.entity.portfolio_id for x in preg.all_draft()] == [p.portfolio_id]
        assert preg.all_live() == []


class TestAKB:
    def test_allocated_to_relationship_created(self):
        e = edge("EDGE-A")
        policy = PortfolioPolicy(
            "policy_v1", max_edges=5, weighting_method=WeightingMethod.EQUAL_WEIGHT
        )
        akb = akb_with_edges(e)
        p = PortfolioBuilder(policy, edge_registry(e), PortfolioRegistry(), akb).create(
            [("EDGE-A", SignalDirection.LONG)]
        )
        assert akb.get_node(NodeType.PORTFOLIO, p.portfolio_id).payload == p
        rels = akb.relationships_from(
            NodeType.EDGE, "EDGE-A", RelationshipType.ALLOCATED_TO
        )
        assert [(r.source_id, r.target_id) for r in rels] == [
            ("EDGE-A", p.portfolio_id)
        ]

    def test_no_production_decision_created(self):
        e = edge("EDGE-A")
        policy = PortfolioPolicy(
            "policy_v1", max_edges=5, weighting_method=WeightingMethod.EQUAL_WEIGHT
        )
        akb = akb_with_edges(e)
        PortfolioBuilder(policy, edge_registry(e), PortfolioRegistry(), akb).create(
            [("EDGE-A", SignalDirection.LONG)]
        )
        assert not [n for n in akb.nodes if n[0] == NodeType.PRODUCTION_DECISION]


class TestPortfolioAllocationInvariants:
    def test_rejects_zero_or_negative_weight(self):
        with pytest.raises(ValueError, match="weight must be > 0"):
            PortfolioAllocation("E1", 0.0, SignalDirection.LONG)
        with pytest.raises(ValueError, match="weight must be > 0"):
            PortfolioAllocation("E1", -0.1, SignalDirection.LONG)

    def test_rejects_weights_not_summing_to_one(self):
        allocations = (
            PortfolioAllocation("E1", 0.5, SignalDirection.LONG),
            PortfolioAllocation("E2", 0.6, SignalDirection.LONG),
        )
        with pytest.raises(ValueError, match="sum to 1.0"):
            Portfolio(portfolio_id="p1", allocations=allocations)

    def test_rejects_duplicate_edge_in_contract(self):
        allocations = (
            PortfolioAllocation("E1", 0.5, SignalDirection.LONG),
            PortfolioAllocation("E1", 0.5, SignalDirection.SHORT),
        )
        with pytest.raises(ValueError, match="duplicate edge"):
            Portfolio(portfolio_id="p1", allocations=allocations)

    def test_accepts_valid_empty_allocations_in_contract(self):
        p = Portfolio(portfolio_id="p1", allocations=())
        assert p.allocations == ()
