# Specification: Walk Forward Validator

Derived from: ADR-007 (Experiment Protocol), ADR-001 (Determinism),
ADR-000B (Trust Model)
Constitution: be37bf97... (Freeze v1.0, 2026-07-29)

Status: Draft (v0.1)

## 1. Purpose

WalkForwardValidator answers the question that in-sample metrics
cannot: "does this edge survive on data never seen during training?"

It splits a snapshot into train/test windows in time order, evaluates
the rule on each train slice (building feature context from that slice
ONLY — no lookahead), then evaluates the same rule on the following
test slice using the train-derived context.

## 2. Input

```text
dataset_id
rule (canonical AST text, e.g. "(GT RSI_14_CLOSE P80)")
rows (list[dict]: ts, symbol, exchange, tier, features, label_RETURN_1h)
windows (tuple[WFWindow, ...])
```

```python
@dataclass(frozen=True, slots=True)
class WFWindow:
    train_start: int   # ts (epoch ms), inclusive
    train_end: int     # exclusive
    test_start: int    # inclusive
    test_end: int      # exclusive
```

Windows are time-ordered. The validator does NOT reorder them.

## 3. Per-window evaluation

```text
train_rows = rows where train_start <= ts < train_end
ctx        = feature context (per-symbol mean/sd) computed from train_rows ONLY
is_returns = label_RETURN_1h of train_rows where rule fires (ctx from same slice)
oos_returns= label_RETURN_1h of test_rows where rule fires (ctx from TRAIN slice)

is_sharpe  = compute_metrics(is_returns,  n_train)["sharpe"]
oos_sharpe = compute_metrics(oos_returns, n_test)["sharpe"]

pass_w     = oos_sharpe > 0
```

No-lookahead invariant: test rows are never part of the context.

## 4. Aggregate result

```python
@dataclass(frozen=True, slots=True)
class WalkForwardResult:
    rule: str
    dataset_id: str
    is_sharpe_mean: float      # mean is_sharpe over windows
    oos_sharpe_mean: float     # mean oos_sharpe over windows
    stability: float           # see formula below
    passes: int                # windows with oos_sharpe > 0
    fails: int                 # windows - passes
    window_sharpe_ratios: tuple[float, ...]   # per-window clamp01(oos/is)
    window_oos_sharpes: tuple[float, ...]     # per-window raw OOS sharpe
```

## 5. Stability

```text
per-window ratio = clamp01(oos_sharpe_w / max(is_sharpe_w, 1e-9))
stability        = mean(ratio over PASSING windows)   # 0.0 if passes == 0
```

Intuition: how close OOS performance stays to in-sample performance,
averaged over windows that actually passed. Always in [0, 1].

(Note: the "0.81" in the earlier discussion was illustrative; the
formula above is the normative one.)

## 6. Edge cases (fail-closed, ADR-000B)

- Empty `windows` → ValueError.
- Window with empty train slice → ValueError (cannot build context).
- Window with empty test slice → oos_sharpe = 0 → fail window (valid
  outcome, not an error).
- Rule never fires on a slice → trade_count 0 → sharpe 0.

## 7. Determinism

Same (dataset_id, rule, rows, windows) → identical result. No
randomness; iteration follows input order.

## 8. Acceptance criteria

- per-window slicing correct (ts boundaries)
- context built from train slice only (no lookahead)
- pass/fail by oos_sharpe > 0
- stability = mean ratio over passing windows
- empty windows → ValueError
- deterministic (two identical runs → equal)
- aggregates: is/oos sharpe means, passes + fails == len(windows)
