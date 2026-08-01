"""AlphaOS Portfolio: immutable collection of ACTIVE Edges only.

Portfolio performs knowledge selection, not risk, sizing, execution,
rebalancing, or ProductionDecision.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum

from .akb import AKB, NodeType
from .contracts import (
    EdgeStatus,
    Portfolio,
    PortfolioAllocation,
    PortfolioStatus,
    RelationshipType,
    SignalDirection,
)
from .registries import EdgeRegistry, PortfolioRegistry


class WeightingMethod(str, Enum):
    EQUAL_WEIGHT = "equal_weight"


class PortfolioError(ValueError):
    """Portfolio invariant violation."""


@dataclass(frozen=True, slots=True)
class PortfolioPolicy:
    policy_id: str
    max_edges: int
    weighting_method: WeightingMethod = WeightingMethod.EQUAL_WEIGHT


def portfolio_id(policy_id: str, allocs: tuple[tuple[str, SignalDirection], ...]) -> str:
    """Deterministic id from policy + sorted (edge_id, direction) pairs."""
    body = json.dumps(
        {"policy_id": policy_id, "allocations": sorted(allocs, key=lambda x: x[0])},
        sort_keys=True,
    )
    return f"PORT-{hashlib.sha256(body.encode('utf-8')).hexdigest()[:20]}"


class PortfolioBuilder:
    def __init__(self, policy: PortfolioPolicy, edge_registry: EdgeRegistry,
                 portfolio_registry: PortfolioRegistry, akb: AKB) -> None:
        self.policy = policy
        self.edge_registry = edge_registry
        self.portfolio_registry = portfolio_registry
        self.akb = akb

    def create(self, alloc_requests: list[tuple[str, SignalDirection]]) -> Portfolio:
        ordered = tuple(sorted(alloc_requests, key=lambda x: x[0]))
        self._validate_membership(ordered)
        weight = 1.0 / len(ordered)
        allocations = tuple(
            PortfolioAllocation(edge_id, weight, direction)
            for edge_id, direction in ordered
        )
        portfolio = Portfolio(
            portfolio_id=portfolio_id(self.policy.policy_id, ordered),
            policy_id=self.policy.policy_id,
            allocations=allocations,
            status=PortfolioStatus.DRAFT,
        )
        self.portfolio_registry.register(portfolio)
        self.akb.add_node(NodeType.PORTFOLIO, portfolio.portfolio_id, portfolio)
        for edge_id, _ in ordered:
            self.akb.add_relationship(RelationshipType.ALLOCATED_TO,
                                      NodeType.EDGE, edge_id,
                                      NodeType.PORTFOLIO, portfolio.portfolio_id)
        return portfolio

    def _validate_membership(self, allocs: tuple[tuple[str, SignalDirection], ...]) -> None:
        if not allocs:
            raise PortfolioError("Portfolio requires at least one ACTIVE edge")
        edge_ids = [edge_id for edge_id, _ in allocs]
        if len(set(edge_ids)) != len(edge_ids):
            raise PortfolioError("duplicate edge in portfolio")
        if len(allocs) > self.policy.max_edges:
            raise PortfolioError("max_edges exceeded")
        if self.policy.weighting_method != WeightingMethod.EQUAL_WEIGHT:
            raise PortfolioError("only equal_weight supported in this stage")
        for edge_id, _ in allocs:
            edge = self.edge_registry.get(edge_id)
            if edge.status != EdgeStatus.ACTIVE:
                raise PortfolioError(f"edge must be ACTIVE: {edge_id}")
