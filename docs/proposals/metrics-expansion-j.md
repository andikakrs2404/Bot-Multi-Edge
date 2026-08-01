# Proposal: Experiment Metrics Expansion (Commit J)

Date: 2026-08-01
Status: PROPOSED — awaiting architectural review
Author: assistant (Hermes)
Reviewer: user (Chief Architect)

## 1. Problem

`ExperimentRunner` currently emits only:

```python
{"sample": ..., "hit_rate": ...}
```

The EdgeRanker consumes `sharpe / profit_factor / max_drawdown / coverage`.
With only binary `label_HIT_TARGET` available, these metrics cannot be
computed meaningfully — they degenerate to functions of hit_rate, all
correlated ~1.0. Ranking would be theater, not evidence.

## 2. Root cause

Snapshot parquet has `label_HIT_TARGET` (0/1) but no per-row forward
return. Sharpe/PF/MaxDD require a return series, not a binary label.

## 3. Decision required: data contract change

### Option A — hit-based (no schema change)

Win = +1, loss = -1 constant returns.

- Deterministic, testable, zero data impact.
- BUT all metrics correlate 100% with hit_rate → ranking meaningless.
- Rejected: does not solve the identified gap.

### Option B — return-based (schema change) [RECOMMENDED]

Snapshot gains a required forward-return column per row:

```text
label_RETURN_1h   # forward 1-bar return, only meaningful where HIT_TARGET=1
```

Runner computes from the return series of matched rows:

```text
sharpe         = mean(returns) / (std(returns) + eps) * sqrt(annualizer)
profit_factor  = gross_win / abs(gross_loss)
max_drawdown   = max peak-to-trough of cumulative returns
coverage       = n_matched / n_total_rows
win_rate       = n_win / n_matched
expectancy     = mean(returns)
trade_count    = n_matched
```

Fail-closed: snapshot without `label_RETURN_1h` → exception, no silent
zero-fill (ADR-000B).

## 4. Scope

- `shared/experiment.py`: metrics computation (pure function, unit-testable)
- `shared/experiment.py`: runner emits full metrics dict
- `tests/`: fixture snapshot with return column + metric tests
- `docs/specifications/experiment-protocol.md`: document metrics + schema
- `docs/specifications/edge-ranker.md`: note metrics source contract

Out of scope (future commits): walk-forward (K), stability (L), clustering (M),
portfolio research (N), Monte Carlo, regime-aware.

## 5. Metric formulas (deterministic, documented)

Given matched rows with returns r_1..r_n (n = trade_count):

```text
expectancy   = mean(r)
win_rate     = count(r > 0) / n
profit_factor= sum(r > 0) / -sum(r < 0)     # inf if no losses → cap? NO, keep inf
sharpe       = mean(r) / (std(r, ddof=1) or tiny) * sqrt(trades_per_year)
max_drawdown = -min over k of (cum_k / peak_k - 1)   # positive number
coverage     = n / N_total_rows
```

Decision needed:
1. `profit_factor` when gross_loss == 0 → `inf` or capped? (rank comparison with inf works, JSON serialization does not — evidence_id hashes metrics via json.dumps)
2. `trades_per_year` annualizer: constant? per-timeframe mapping? v0.1 constant 252?
3. `max_drawdown` sign: store positive (rank penalizes with `- dd_weight * dd`)? Consistent with ranker current behavior.

## 6. Impact

- Snapshot fixtures must gain `label_RETURN_1h` → tests updated
- evidence_id changes (hashes metrics) → downstream IDs change, fine (content-addressed)
- No production-domain impact

## 7. Acceptance criteria (proposed)

- metrics present: sharpe, profit_factor, max_drawdown, coverage, win_rate, expectancy, trade_count
- pure function: `compute_metrics(returns, n_total) -> dict`
- deterministic: same input → same metrics
- fail-closed: missing return column → ValueError
- edge case: n=0 → metrics zeros + trade_count=0 (not exception)
- ranker: meaningful differentiation when sharpe/pf differ
