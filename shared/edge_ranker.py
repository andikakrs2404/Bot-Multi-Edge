"""AlphaOS EdgeRanker: weighted metric ranking of eligible Edges.

Ranks VALIDATED/ACTIVE Edges by weighted score from supporting Evidence
metrics. Answers "which edge is best?" for Activation/Portfolio selection.
Deterministic: tie-break by edge_id.
"""

from __future__ import annotations

from dataclasses import dataclass

from .contracts import Edge, EdgeStatus
from .evidence import EvidenceRegistry
from .registry import UnknownIdentityError


class RankEdgeError(ValueError):
    """Edge ranking invariant violation."""


@dataclass(frozen=True, slots=True)
class RankingPolicy:
    policy_id: str
    sharpe_weight: float
    pf_weight: float
    dd_weight: float
    coverage_weight: float


DEFAULT_RANKING_POLICY = RankingPolicy(
    policy_id="default", sharpe_weight=1.0, pf_weight=1.0,
    dd_weight=1.0, coverage_weight=1.0)


@dataclass(frozen=True, slots=True)
class RankedEdge:
    edge_id: str
    score: float
    rank: int
    component_scores: dict[str, float]


_ELIGIBLE = {EdgeStatus.VALIDATED, EdgeStatus.ACTIVE}


def rank(edges: tuple[Edge, ...], policy: RankingPolicy,
         evidence_registry: EvidenceRegistry) -> tuple[RankedEdge, ...]:
    """Rank eligible edges by weighted metric score (descending)."""
    if not edges:
        return ()

    scored = []
    for edge in edges:
        if edge.status not in _ELIGIBLE:
            raise RankEdgeError(
                f"edge not eligible for ranking: {edge.edge_id} "
                f"({edge.status.value})")
        try:
            evid = evidence_registry.get(edge.supported_by[0])
        except (UnknownIdentityError, IndexError):
            raise RankEdgeError(
                f"missing evidence for edge: {edge.edge_id}") from None
        m = evid.metrics
        comp = {
            "sharpe": m.get("sharpe", 0.0),
            "pf": m.get("profit_factor", 0.0),
            "dd": m.get("max_drawdown", 0.0),
            "coverage": m.get("coverage", 0.0),
        }
        score = (policy.sharpe_weight * comp["sharpe"]
                 + policy.pf_weight * comp["pf"]
                 - policy.dd_weight * comp["dd"]
                 + policy.coverage_weight * comp["coverage"])
        scored.append((score, edge.edge_id, comp))

    scored.sort(key=lambda x: (-x[0], x[1]))
    return tuple(
        RankedEdge(edge_id=eid, score=score, rank=i + 1, component_scores=comp)
        for i, (score, eid, comp) in enumerate(scored)
    )
