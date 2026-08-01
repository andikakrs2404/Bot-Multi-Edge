"""Tests for AlphaOS WalkForwardValidator (no-lookahead OOS validation)."""

import math

import pytest

from shared.walkforward import (
    WFWindow,
    WalkForwardResult,
    WalkForwardValidator,
)


def make_rows(n_train_windows=4, per_window=200, symbols=("BTCUSDT",)):
    """Synthetic rows: RSI sinusoid, return +1% on hit else -1%.

    Rule (GT RSI_14_CLOSE P80) fires on ~10% of rows. Rows grouped
    into contiguous windows of `per_window` rows per symbol.
    """
    rows = []
    base = 1_700_000_000_000
    step = 1_800_000
    i = 0
    for _ in range(n_train_windows + 1):  # +1 test tail
        for _ in range(per_window):
            for sym in symbols:
                rsi = 50.0 + 40.0 * math.sin(i / 7.0)
                hit = 1.0 if (i % 4 == 0 and rsi > 80) else 0.0
                ret = 0.01 if hit else -0.01
                rows.append({"ts": base + i * step, "symbol": sym,
                             "exchange": "binance_futures", "tier": "A",
                             "RSI_14_CLOSE": rsi,
                             "label_RETURN_1h": ret})
                i += 1
    return rows


def windows_for(rows, per_window=200, n_train=2):
    """Build rolling windows: window w trains on slices w..w+n_train-1."""
    syms = 1  # symbols count in make_rows default
    slice_len = per_window * syms
    ts_slices = sorted({r["ts"] for r in rows})
    slices = [ts_slices[i * slice_len] for i in range(len(ts_slices) // slice_len)]
    out = []
    for i in range(len(slices) - n_train - 1):
        train_start = slices[i]
        train_end = slices[i + n_train]
        test_start = slices[i + n_train]
        test_end = slices[i + n_train + 1]
        out.append(WFWindow(train_start, train_end, test_start, test_end))
    return tuple(out)


RULE = "(GT RSI_14_CLOSE P80)"


class TestWalkForward:
    def test_basic_run(self):
        rows = make_rows(n_train_windows=3, per_window=200)
        wf = WalkForwardValidator()
        res = wf.validate("DS-1", RULE, rows, windows_for(rows, per_window=200))

        assert isinstance(res, WalkForwardResult)
        assert res.rule == RULE
        assert res.dataset_id == "DS-1"
        assert res.passes + res.fails == len(windows_for(rows, per_window=200))
        assert 0.0 <= res.stability <= 1.0

    def test_deterministic(self):
        rows = make_rows()
        wf = WalkForwardValidator()
        a = wf.validate("DS-1", RULE, rows, windows_for(rows))
        b = wf.validate("DS-1", RULE, rows, windows_for(rows))
        assert a == b

    def test_all_positive_oos_windows_pass(self):
        # All test returns positive (with variance) → all windows pass
        rows = make_rows(per_window=200)
        for i, r in enumerate(rows):
            r["label_RETURN_1h"] = 0.01 + 0.002 * (i % 5)
        wf = WalkForwardValidator()
        res = wf.validate("DS-1", RULE, rows, windows_for(rows, per_window=200))

        assert res.passes == len(windows_for(rows, per_window=200))
        assert res.fails == 0

    def test_empty_windows_rejected(self):
        rows = make_rows()
        wf = WalkForwardValidator()
        with pytest.raises(ValueError, match="window"):
            wf.validate("DS-1", RULE, rows, ())

    def test_empty_train_slice_rejected(self):
        rows = make_rows()
        wf = WalkForwardValidator()
        # window entirely after all data
        bad = (WFWindow(10**15, 10**15 + 1, 10**15 + 2, 10**15 + 3),)
        with pytest.raises(ValueError, match="train"):
            wf.validate("DS-1", RULE, rows, bad)

    def test_oos_sharpe_mean_matches_manual(self):
        rows = make_rows(per_window=200)
        wf = WalkForwardValidator()
        wins = windows_for(rows, per_window=200)
        res = wf.validate("DS-1", RULE, rows, wins)

        # recompute: expected oos sharpe mean from a fresh single-window run
        manual = WalkForwardValidator().validate("DS-1", RULE, rows, (wins[0],))
        assert res.window_oos_sharpes[0] == pytest.approx(
            manual.oos_sharpe_mean)
