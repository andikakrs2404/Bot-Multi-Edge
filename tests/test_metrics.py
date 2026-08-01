"""Tests for AlphaOS metric computation (Commit J, return-based metrics)."""

import math

import pytest

from shared.experiment import (
    MAX_PROFIT_FACTOR,
    compute_metrics,
)


class TestComputeMetrics:
    def test_basic_metrics(self):
        returns = [0.01, 0.02, -0.005, 0.015, -0.01, 0.03]
        m = compute_metrics(returns, n_total=100)

        assert m["trade_count"] == 6
        assert m["coverage"] == pytest.approx(6 / 100)
        assert m["hit_rate"] == pytest.approx(4 / 6)
        assert m["expectancy"] == pytest.approx(sum(returns) / 6)

        gross_win = 0.01 + 0.02 + 0.015 + 0.03
        gross_loss = 0.005 + 0.01
        assert m["profit_factor"] == pytest.approx(gross_win / gross_loss)
        assert m["max_drawdown"] >= 0.0
        assert m["sharpe"] == pytest.approx(
            (sum(returns) / 6)
            / (statistics_stdev(returns) or 1e-12)
            * math.sqrt(252))

    def test_empty_returns_zero_metrics(self):
        m = compute_metrics([], n_total=100)

        assert m["trade_count"] == 0
        assert m["coverage"] == 0.0
        assert m["hit_rate"] == 0.0
        assert m["expectancy"] == 0.0
        assert m["profit_factor"] == 0.0
        assert m["max_drawdown"] == 0.0
        assert m["sharpe"] == 0.0

    def test_all_win_profit_factor_capped(self):
        m = compute_metrics([0.01, 0.02, 0.03], n_total=10)

        assert m["profit_factor"] == MAX_PROFIT_FACTOR
        assert m["hit_rate"] == 1.0
        assert m["trade_count"] == 3

    def test_all_loss_profit_factor_zero(self):
        m = compute_metrics([-0.01, -0.02], n_total=10)

        assert m["profit_factor"] == 0.0
        assert m["hit_rate"] == 0.0

    def test_single_constant_return_sharpe_zero(self):
        # constant returns → std=0 → sharpe 0 (no dispersion)
        m = compute_metrics([0.01, 0.01, 0.01], n_total=10)

        assert m["sharpe"] == 0.0
        assert m["hit_rate"] == 1.0

    def test_max_drawdown_positive(self):
        # cum: 0.05, -0.05, -0.03, -0.08 → peak 0.05 → dd 0.13
        returns = [0.05, -0.10, 0.02, -0.05]
        m = compute_metrics(returns, n_total=100)

        assert m["max_drawdown"] == pytest.approx(0.13, abs=1e-9)

    def test_deterministic(self):
        r = [0.01, -0.02, 0.03, -0.01]
        assert compute_metrics(r, n_total=50) == compute_metrics(r, n_total=50)


def statistics_stdev(xs):
    """Sample stdev (ddof=1), matching implementation."""
    n = len(xs)
    if n < 2:
        return 0.0
    mean = sum(xs) / n
    return math.sqrt(sum((x - mean) ** 2 for x in xs) / (n - 1))
