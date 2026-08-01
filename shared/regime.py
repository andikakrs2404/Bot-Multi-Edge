"""AlphaOS RegimeValidator: per-regime edge performance.

Classifies snapshot rows into 6 regimes by return distribution
(trend: UP/DOWN/FLAT × vol: LOW/HIGH), computes rule metrics per
regime, and a robustness score. No OHLC needed — only label_RETURN_1h.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .experiment import _build_context, _eval_row, compute_metrics
from .rules import parse

REGIMES = ("UP_LOW_VOL", "UP_HIGH_VOL", "DOWN_LOW_VOL", "DOWN_HIGH_VOL",
           "FLAT_LOW_VOL", "FLAT_HIGH_VOL")


@dataclass(frozen=True, slots=True)
class RegimePolicy:
    policy_id: str
    block_size: int = 100
    trend_deadzone: float = 0.001
    min_trades: int = 30
    min_coverage: float = 0.01


@dataclass(frozen=True, slots=True)
class RegimeResult:
    regime_metrics: dict[str, dict] = field(default_factory=dict)
    regime_count: int = 6
    supported_regimes: int = 0
    passing_regimes: int = 0
    robustness: float = 0.0


def _classify(mean_r: float, std_r: float, dz: float,
              vol_median: float) -> str:
    trend = "UP" if mean_r > dz else ("DOWN" if mean_r < -dz else "FLAT")
    vol = "HIGH_VOL" if std_r > vol_median else "LOW_VOL"
    return f"{trend}_{vol}"


class RegimeValidator:
    def validate(self, dataset_id: str, rule: str, rows: list[dict],
                 policy: RegimePolicy) -> RegimeResult:
        if not rows:
            raise ValueError("regime validation requires rows")
        ast = parse(rule)
        sorted_rows = sorted(rows, key=lambda r: r["ts"])

        # blocks
        bs = policy.block_size
        blocks = [sorted_rows[i:i + bs]
                  for i in range(0, len(sorted_rows), bs)]

        block_stats = []
        for block in blocks:
            rets = [r["label_RETURN_1h"] for r in block]
            mean_r = sum(rets) / len(rets)
            std_r = (sum((x - mean_r) ** 2 for x in rets) / len(rets)) ** 0.5
            block_stats.append((mean_r, std_r, block))

        vol_median = sorted(s for _, s, _ in block_stats)[len(block_stats) // 2]

        ctx = _build_context(sorted_rows)
        regime_returns: dict[str, list[float]] = {r: [] for r in REGIMES}
        regime_total: dict[str, int] = {r: 0 for r in REGIMES}

        for mean_r, std_r, block in block_stats:
            reg = _classify(mean_r, std_r, policy.trend_deadzone, vol_median)
            regime_returns[reg].extend(
                r["label_RETURN_1h"] for r in block
                if _eval_row(ast, r, ctx))
            regime_total[reg] += len(block)

        metrics = {r: compute_metrics(regime_returns[r], regime_total[r])
                   for r in REGIMES}

        supported = 0
        passing = 0
        for r in REGIMES:
            m = metrics[r]
            if m["trade_count"] >= policy.min_trades:
                supported += 1
                if (m["sharpe"] > 0 and m["profit_factor"] > 1
                        and m["coverage"] > policy.min_coverage):
                    passing += 1

        robustness = passing / supported if supported else 0.0

        return RegimeResult(
            regime_metrics=metrics,
            regime_count=len(REGIMES),
            supported_regimes=supported,
            passing_regimes=passing,
            robustness=robustness,
        )
