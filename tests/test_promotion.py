"""Tests for AlphaOS PromotionEngine (Research → Production gate)."""

import pytest

from shared.contracts import Edge, EdgeStatus
from shared.edge_ranker import RankedEdge
from shared.promotion import (
    PromotionPolicy,
    PromotionResult,
    PromotionVerdict,
    evaluate_promotion,
)
from shared.regime import RegimeResult
from shared.stability import StabilityVerdict


def edge(status=EdgeStatus.VALIDATED) -> Edge:
    return Edge(edge_id="EDGE-1", rule_id="RULE-1", experiment_id="EXP-1",
                supported_by=("EVID-1",), status=status)


def ranked(score=2.0) -> RankedEdge:
    return RankedEdge(edge_id="EDGE-1", score=score, rank=1,
                      component_scores={})


def stability(verdict="STABLE", value=0.8) -> StabilityVerdict:
    return StabilityVerdict(rule="RULE-1", dataset_id="DS-1",
                            verdict=verdict, pass_ratio=0.8,
                            stability=value, oos_sharpe_mean=1.3,
                            reasons=())

def regime(robustness=0.75) -> RegimeResult:
    return RegimeResult(regime_metrics={}, regime_count=6,
                        supported_regimes=6, passing_regimes=6,
                        robustness=robustness)


POL = PromotionPolicy("pol", min_rank_score=1.5, min_stability=0.75,
                      min_regime_robustness=0.70)


class TestPromotion:
    def test_promotable_all_gates_met(self):
        r = evaluate_promotion(edge(), ranked(2.0), stability(0.8),
                               regime(0.75), POL)
        assert r.verdict == PromotionVerdict.PROMOTABLE
        assert r.reasons == ()

    def test_not_validated(self):
        r = evaluate_promotion(edge(EdgeStatus.ACTIVE), ranked(2.0),
                               stability(0.8), regime(0.75), POL)
        assert r.verdict == PromotionVerdict.NON_PROMOTABLE
        assert r.reasons == ("not_validated",)

    def test_require_validated_false_allows_active(self):
        pol = PromotionPolicy("p2", 1.5, 0.75, 0.70, require_validated=False)
        r = evaluate_promotion(edge(EdgeStatus.ACTIVE), ranked(2.0),
                               stability(0.8), regime(0.75), pol)
        assert r.verdict == PromotionVerdict.PROMOTABLE

    def test_low_rank(self):
        r = evaluate_promotion(edge(), ranked(1.0), stability(0.8),
                               regime(0.75), POL)
        assert r.reasons == ("rank_score_below_threshold",)

    def test_unstable(self):
        r = evaluate_promotion(edge(), ranked(2.0), stability(value=0.5),
                               regime(0.75), POL)
        assert r.reasons == ("unstable",)

    def test_regime_not_robust(self):
        r = evaluate_promotion(edge(), ranked(2.0), stability(0.8),
                               regime(0.4), POL)
        assert r.reasons == ("regime_not_robust",)

    def test_multiple_failures_fixed_order(self):
        r = evaluate_promotion(edge(EdgeStatus.RETIRED), ranked(0.5),
                               stability(value=0.4), regime(0.3), POL)
        assert r.reasons == ("not_validated", "rank_score_below_threshold",
                             "unstable", "regime_not_robust")

    def test_boundary_passes(self):
        r = evaluate_promotion(edge(), ranked(1.5), stability(value=0.75),
                               regime(0.70), POL)
        assert r.verdict == PromotionVerdict.PROMOTABLE

    def test_nan_fails(self):
        r = evaluate_promotion(edge(), ranked(2.0), stability(0.8),
                               regime(float("nan")), POL)
        assert r.verdict == PromotionVerdict.NON_PROMOTABLE
        assert "regime_not_robust" in r.reasons

    def test_deterministic(self):
        e, rk, st, rg = edge(), ranked(2.0), stability(0.8), regime(0.75)
        assert evaluate_promotion(e, rk, st, rg, POL) == \
            evaluate_promotion(e, rk, st, rg, POL)
