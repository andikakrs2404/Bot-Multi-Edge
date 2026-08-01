# Specification: Regime Validator

Derived from: ADR-000B (Trust Model), ADR-001 (Determinism)
Constitution: be37bf97... (Freeze v1.0, 2026-07-29)

Status: Draft (v0.1)

## 1. Purpose

RegimeValidator tests an edge across market regimes. An edge can look
great on aggregate metrics while being a "bull market hero" — profitable
only in one regime. This engine reports per-regime performance and a
robustness score.

No OHLC required. Regime classification uses ONLY `label_RETURN_1h`
already present in the snapshot.

## 2. Regime classification

Rows are sorted by `ts` (deterministic), then split into contiguous
blocks of `block_size` rows (tail block kept as-is).

Per block:

```text
mean_r = mean(label_RETURN_1h over block rows)
std_r  = std(label_RETURN_1h over block rows)

trend:  mean_r >  +dz          → UP
        mean_r <  -dz          → DOWN
        else                   → FLAT

vol:    std_r >  median(all block std_r)  → HIGH
        else                                → LOW
```

`dz` (dead-zone) comes from RegimePolicy; vol split is the median of
all block stds (relative, deterministic).

6 regimes: `UP_LOW_VOL, UP_HIGH_VOL, DOWN_LOW_VOL, DOWN_HIGH_VOL,
FLAT_LOW_VOL, FLAT_HIGH_VOL`.

## 3. RegimePolicy

```python
@dataclass(frozen=True, slots=True)
class RegimePolicy:
    policy_id: str
    block_size: int = 100
    trend_deadzone: float = 0.001
    min_trades: int = 30
    min_coverage: float = 0.01
```

## 4. Per-regime metrics

Rule is evaluated with the global snapshot context (same semantics as
ExperimentRunner). Returns of matched rows within each regime's blocks
are pooled:

```text
metrics[regime] = compute_metrics(returns_regime, n_total_rows)
```

## 5. Pass criteria & robustness

```text
supported = trade_count >= min_trades
pass      = supported AND sharpe > 0 AND pf > 1 AND coverage > min_coverage
robustness = passing_regimes / supported_regimes      # 0.0 if none supported
```

## 6. RegimeResult

```python
@dataclass(frozen=True, slots=True)
class RegimeResult:
    regime_metrics: dict[str, dict]   # regime → metrics dict
    regime_count: int                 # 6
    supported_regimes: int
    passing_regimes: int
    robustness: float
```

## 7. Edge cases (fail-closed)

- Empty rows → ValueError.
- Fewer rows than block_size → single block; classification still works.
- Zero supported regimes → robustness 0.0 (valid, not error).

## 8. Determinism

Same (dataset_id, rule, rows, policy) → identical result. Sort by ts is
stable; no randomness.

## 9. Acceptance criteria

- 6 regimes always present in regime_metrics
- trend/vol classification matches block statistics
- pass = sharpe>0 AND pf>1 AND coverage>min_coverage (strict)
- robustness = passing/supported
- empty rows → ValueError
- deterministic twice
