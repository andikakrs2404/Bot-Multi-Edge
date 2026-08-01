"""Tests for AlphaOS StabilityEngine (WF result → STABLE/UNSTABLE)."""

import pytest

from shared.stability import (
    StabilityPolicy,
    StabilityVerdict,
    evaluate_stability,
)
from shared.walkforward import WalkForwardResult


def wf(stability=0.8, passes=5, fails=1, oos_sharpe=1.3,
       is_sharpe=1.7, n_windows=None):
    n = n_windows if n_windows is not None else passes + fails
    return WalkForwardResult(
        rule="(GT RSI_14_CLOSE P80)", dataset_id="DS-1",
        is_sharpe_mean=is_sharpe, oos_sharpe_mean=oos_sharpe,
        stability=stability, passes=passes, fails=fails,
        window_sharpe_ratios=(0.8,) * passes, window_oos_sharpes=(1.3,) * n,
    )


POL = StabilityPolicy("pol", min_stability=0.75, min_pass_ratio=0.70,
                      min_oos_sharpe=1.0)


class TestVerdict:
    def test_stable_when_all_pass(self):
        v = evaluate_stability(wf(stability=0.8, passes=5, fails=1,
                                  oos_sharpe=1.3), POL)
        assert v.verdict == "STABLE"
        assert v.reasons == ()
        assert v.pass_ratio == pytest.approx(5 / 6)

    def test_unstable_low_stability(self):
        v = evaluate_stability(wf(stability=0.5, passes=5, fails=1,
                                  oos_sharpe=1.3), POL)
        assert v.verdict == "UNSTABLE"
        assert any("stability" in r for r in v.reasons)

    def test_unstable_low_pass_ratio(self):
        v = evaluate_stability(wf(stability=0.8, passes=2, fails=4,
                                  oos_sharpe=1.3), POL)
        assert v.verdict == "UNSTABLE"
        assert any("pass_ratio" in r for r in v.reasons)

    def test_unstable_low_oos_sharpe(self):
        v = evaluate_stability(wf(stability=0.8, passes=5, fails=1,
                                  oos_sharpe=0.4), POL)
        assert v.verdict == "UNSTABLE"
        assert any("oos_sharpe" in r for r in v.reasons)

    def test_multiple_failures_fixed_order(self):
        v = evaluate_stability(wf(stability=0.5, passes=2, fails=4,
                                  oos_sharpe=0.4), POL)
        assert v.verdict == "UNSTABLE"
        order = [r for r in v.reasons]
        assert "stability" in order
        assert "pass_ratio" in order
        assert "oos_sharpe" in order
        assert order.index("stability") < order.index("pass_ratio") \
            < order.index("oos_sharpe")

    def test_boundary_exact_threshold_passes(self):
        v = evaluate_stability(wf(stability=0.75, passes=7, fails=3,
                                  oos_sharpe=1.0), POL)
        assert v.verdict == "STABLE"

    def test_deterministic(self):
        r = wf()
        assert evaluate_stability(r, POL) == evaluate_stability(r, POL)

    def test_nan_fails(self):
        v = evaluate_stability(wf(stability=float("nan"), passes=5,
                                  fails=1, oos_sharpe=1.3), POL)
        assert v.verdict == "UNSTABLE"

    def test_zero_windows_defensive(self):
        r = WalkForwardResult(rule="R", dataset_id="D", is_sharpe_mean=0.0,
                              oos_sharpe_mean=0.0, stability=0.0,
                              passes=0, fails=0, window_sharpe_ratios=(),
                              window_oos_sharpes=())
        v = evaluate_stability(r, POL)
        assert v.verdict == "UNSTABLE"
        assert v.pass_ratio == 0.0
