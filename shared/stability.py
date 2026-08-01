"""AlphaOS StabilityEngine: WalkForwardResult → STABLE/UNSTABLE.

Formal decision layer on top of walk-forward numbers: does this edge
hold up out-of-sample? Pure function of inputs, deterministic.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .walkforward import WalkForwardResult


@dataclass(frozen=True, slots=True)
class StabilityPolicy:
    policy_id: str
    min_stability: float = 0.75
    min_pass_ratio: float = 0.70
    min_oos_sharpe: float = 1.0


@dataclass(frozen=True, slots=True)
class StabilityVerdict:
    rule: str
    dataset_id: str
    verdict: str
    pass_ratio: float
    stability: float
    oos_sharpe_mean: float
    reasons: tuple[str, ...]


def evaluate_stability(result: WalkForwardResult,
                       policy: StabilityPolicy) -> StabilityVerdict:
    """Verdict: STABLE iff all thresholds met (>=). Fail-closed on NaN."""
    n = result.passes + result.fails
    pass_ratio = result.passes / n if n else 0.0

    def ok(value: float, minimum: float) -> bool:
        return not math.isnan(value) and value >= minimum

    reasons: list[str] = []
    if not ok(result.stability, policy.min_stability):
        reasons.append("stability")
    if not ok(pass_ratio, policy.min_pass_ratio):
        reasons.append("pass_ratio")
    if not ok(result.oos_sharpe_mean, policy.min_oos_sharpe):
        reasons.append("oos_sharpe")

    return StabilityVerdict(
        rule=result.rule,
        dataset_id=result.dataset_id,
        verdict="STABLE" if not reasons else "UNSTABLE",
        pass_ratio=pass_ratio,
        stability=result.stability,
        oos_sharpe_mean=result.oos_sharpe_mean,
        reasons=tuple(reasons),
    )
