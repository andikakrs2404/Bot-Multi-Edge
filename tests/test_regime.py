"""Tests for AlphaOS RegimeValidator (per-regime edge performance)."""

import math

import pytest

from shared.regime import (
    RegimePolicy,
    RegimeResult,
    RegimeValidator,
)


def make_rows(blocks=6, block_size=100):
    """Rows with regime-controllable returns.

    Block b gets returns = base_b + jitter. base_b chosen by caller
    mutating rows afterwards (see fixtures).
    """
    rows = []
    i = 0
    for b in range(blocks):
        for j in range(block_size):
            ts = 1_700_000_000_000 + i * 1_800_000
            rsi = 50.0 + 40.0 * math.sin(i / 7.0)
            hit = 1.0 if (i % 4 == 0 and rsi > 80) else 0.0
            ret = 0.01 if hit else -0.01
            rows.append({"ts": ts, "symbol": "BTCUSDT",
                         "exchange": "binance_futures", "tier": "A",
                         "RSI_14_CLOSE": rsi, "label_RETURN_1h": ret,
                         "_block": b})
            i += 1
    return rows


def set_block_returns(rows, block, base, jitter=0.005):
    for r in rows:
        if r["_block"] == block:
            r["label_RETURN_1h"] = base + jitter * ((r["ts"] // 1_800_000) % 3)


RULE = "(GT RSI_14_CLOSE P80)"
POL = RegimePolicy("pol", block_size=100, trend_deadzone=0.001,
                   min_trades=5, min_coverage=0.0)


class TestRegimeValidator:
    def test_six_regimes_present(self):
        rows = make_rows()
        rv = RegimeValidator()
        res = rv.validate("DS-1", RULE, rows, POL)

        assert isinstance(res, RegimeResult)
        assert res.regime_count == 6
        assert set(res.regime_metrics.keys()) == {
            "UP_LOW_VOL", "UP_HIGH_VOL", "DOWN_LOW_VOL", "DOWN_HIGH_VOL",
            "FLAT_LOW_VOL", "FLAT_HIGH_VOL"}

    def test_trend_classification(self):
        rows = make_rows()
        # block 0: strong up (mean 0.02), block 1: strong down (-0.02)
        set_block_returns(rows, 0, 0.02, jitter=0.001)
        set_block_returns(rows, 1, -0.02, jitter=0.001)
        rv = RegimeValidator()

        # classify block 0 and 1 via internal split — assert via regime metrics
        res = rv.validate("DS-1", RULE, rows, POL)
        # block 0 UP regime must exist with positive sharpe somewhere
        up_keys = [k for k in res.regime_metrics if k.startswith("UP_")]
        down_keys = [k for k in res.regime_metrics if k.startswith("DOWN_")]
        assert up_keys and down_keys
        assert any(res.regime_metrics[k]["trade_count"] > 0 for k in up_keys)
        assert any(res.regime_metrics[k]["trade_count"] > 0 for k in down_keys)

    def test_flat_regime(self):
        rows = make_rows()
        for r in rows:
            r["label_RETURN_1h"] = 0.001 * ((r["ts"] // 1_800_000) % 3)
        rv = RegimeValidator()
        res = rv.validate("DS-1", RULE, rows, POL)

        flat_keys = [k for k in res.regime_metrics if k.startswith("FLAT_")]
        assert flat_keys

    def test_robustness_all_pass(self):
        rows = make_rows()
        for r in rows:
            r["label_RETURN_1h"] = 0.01 + 0.002 * (r["ts"] // 1_800_000 % 3)
        rv = RegimeValidator()
        res = rv.validate("DS-1", RULE, rows, POL)

        assert res.robustness == pytest.approx(
            res.passing_regimes / res.supported_regimes)
        assert res.passing_regimes >= 1

    def test_robustness_zero_when_no_support(self):
        rows = make_rows()
        rv = RegimeValidator()
        pol = RegimePolicy("p", block_size=100, trend_deadzone=0.001,
                           min_trades=10**6, min_coverage=0.0)
        res = rv.validate("DS-1", RULE, rows, pol)

        assert res.supported_regimes == 0
        assert res.robustness == 0.0

    def test_empty_rows_rejected(self):
        rv = RegimeValidator()
        with pytest.raises(ValueError):
            rv.validate("DS-1", RULE, [], POL)

    def test_deterministic(self):
        rows = make_rows()
        rv = RegimeValidator()
        a = rv.validate("DS-1", RULE, rows, POL)
        b = rv.validate("DS-1", RULE, rows, POL)
        assert a == b

    def test_pass_criteria_strict(self):
        rows = make_rows()
        rv = RegimeValidator()
        res = rv.validate("DS-1", RULE, rows, POL)

        expected_passing = sum(
            1 for m in res.regime_metrics.values()
            if m["trade_count"] >= POL.min_trades
            and m["sharpe"] > 0 and m["profit_factor"] > 1
            and m["coverage"] > POL.min_coverage)
        assert res.passing_regimes == expected_passing
