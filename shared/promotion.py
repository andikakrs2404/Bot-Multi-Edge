"""AlphaOS PromotionEngine: formal Research → Production gate.

Combines every validation signal (edge status, rank score, stability,
regime robustness) into one objective verdict: PROMOTABLE or
NON_PROMOTABLE. Pure function, deterministic.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

from .contracts import Edge, EdgeStatus
from .edge_ranker import RankedEdge
from .regime import RegimeResult
from .stability import StabilityVerdict


class PromotionVerdict(str, Enum):
    PROMOTABLE = "PROMOTABLE"
    NON_PROMOTABLE = "NON_PROMOTABLE"


@dataclass(frozen=True, slots=True)
class PromotionPolicy:
    policy_id: str
    min_rank_score: float
    min_stability: float
    min_regime_robustness: float
    require_validated: bool = True


@dataclass(frozen=True, slots=True)
class PromotionResult:
    edge_id: str
    verdict: PromotionVerdict
    reasons: tuple[str, ...]


def evaluate_promotion(edge: Edge, ranked: RankedEdge,
                       stability: StabilityVerdict, regime: RegimeResult,
                       policy: PromotionPolicy) -> PromotionResult:
    """Verdict: PROMOTABLE iff all gates met (>=). Fail-closed on NaN."""

    def ok(value: float, minimum: float) -> bool:
        return not math.isnan(value) and value >= minimum

    reasons: list[str] = []
    if policy.require_validated and edge.status != EdgeStatus.VALIDATED:
        reasons.append("not_validated")
    if not ok(ranked.score, policy.min_rank_score):
        reasons.append("rank_score_below_threshold")
    if not ok(stability.stability, policy.min_stability):
        reasons.append("unstable")
    if not ok(regime.robustness, policy.min_regime_robustness):
        reasons.append("regime_not_robust")

    return PromotionResult(
        edge_id=edge.edge_id,
        verdict=(PromotionVerdict.PROMOTABLE if not reasons
                 else PromotionVerdict.NON_PROMOTABLE),
        reasons=tuple(reasons),
    )
