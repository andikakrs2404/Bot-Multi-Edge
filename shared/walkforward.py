"""AlphaOS WalkForwardValidator: no-lookahead OOS validation.

Answers: does this edge survive on data never seen during training?
Evaluates a rule on rolling train/test windows. Feature context is
built from the TRAIN slice only — test rows never leak into context.
"""

from __future__ import annotations

from dataclasses import dataclass

from .experiment import _build_context, _eval_row, compute_metrics
from .rules import parse


@dataclass(frozen=True, slots=True)
class WFWindow:
    train_start: int
    train_end: int
    test_start: int
    test_end: int


@dataclass(frozen=True, slots=True)
class WalkForwardResult:
    rule: str
    dataset_id: str
    is_sharpe_mean: float
    oos_sharpe_mean: float
    stability: float
    passes: int
    fails: int
    window_sharpe_ratios: tuple[float, ...]
    window_oos_sharpes: tuple[float, ...]


class WalkForwardValidator:
    def validate(self, dataset_id: str, rule: str, rows: list[dict],
                 windows: tuple[WFWindow, ...]) -> WalkForwardResult:
        if not windows:
            raise ValueError("walk-forward requires at least one window")
        ast = parse(rule)

        is_sharpes: list[float] = []
        oos_sharpes: list[float] = []
        ratios: list[float] = []

        for w in windows:
            train_rows = [r for r in rows
                          if w.train_start <= r["ts"] < w.train_end]
            if not train_rows:
                raise ValueError(
                    f"window train slice empty: {w.train_start}..{w.train_end}")
            ctx = _build_context(train_rows)

            is_returns = [r["label_RETURN_1h"] for r in train_rows
                          if _eval_row(ast, r, ctx)]
            is_sharpe = compute_metrics(is_returns, len(train_rows))["sharpe"]

            test_rows = [r for r in rows
                         if w.test_start <= r["ts"] < w.test_end]
            oos_returns = [r["label_RETURN_1h"] for r in test_rows
                           if _eval_row(ast, r, ctx)]
            oos_sharpe = compute_metrics(oos_returns, len(test_rows))["sharpe"]

            is_sharpes.append(is_sharpe)
            oos_sharpes.append(oos_sharpe)

        for is_s, oos_s in zip(is_sharpes, oos_sharpes):
            if oos_s > 0:
                denom = max(is_s, 1e-9)
                ratios.append(min(1.0, oos_s / denom))

        passes = sum(1 for s in oos_sharpes if s > 0)
        n = len(windows)
        stability = (sum(ratios) / len(ratios)) if ratios else 0.0

        return WalkForwardResult(
            rule=rule,
            dataset_id=dataset_id,
            is_sharpe_mean=sum(is_sharpes) / n,
            oos_sharpe_mean=sum(oos_sharpes) / n,
            stability=stability,
            passes=passes,
            fails=n - passes,
            window_sharpe_ratios=tuple(ratios),
            window_oos_sharpes=tuple(oos_sharpes),
        )
