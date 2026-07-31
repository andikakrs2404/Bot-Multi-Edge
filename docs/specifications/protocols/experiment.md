# Specification: Experiment Protocol (Field-Level)

Derived from: ADR-007 (Experiment Protocol), ADR-008 (Evidence Model)

Status: Draft (v0.1)

## ExperimentConfig

```yaml
experiment_id: EXP-YYYY-NNNN
constitution_hash: "sha256..."        # ADR-001A
git_commit: "..."                      # full SHA
runtime: {python: "3.11.x", duckdb: "1.x", ...}
seeds: {numpy: 42, random: 42}
dataset_ids: ["sha256...", ...]        # ADR-004
registry_versions: {features: "v1", labels: "v1", rules: "v1"}
rule_set: [...]                        # canonical AST serializations (ADR-006)
optimizer: {method: "bayesian", budget: 1000, ...}
validation: {walk_forward: {...}, oos_ratio: 0.2, ...}
```

## CandidateResult

| Field | Type |
| --- | --- |
| `candidate_id` | string (local to experiment) |
| `rule_id` | string (content hash) |
| `label_id` | string |
| `metrics` | map — canonical metrics (below) |
| `status` | PASS / FAIL / OVERFIT |
| `evidence_bundle_ref` | string (artifact hash) |

## Canonical Metrics (computed identically everywhere)

| Metric | Formula (canonical) |
| --- | --- |
| win_rate | n(return > 0) / n |
| profit_factor | gross_profit / |gross_loss| |
| expectancy | mean(return per trade) |
| sharpe | mean(r)/std(r) * sqrt(periods_per_year) |
| sortino | mean(r)/downside_std(r) * sqrt(periods_per_year) |
| max_drawdown | max peak-to-trough decline on equity curve |
| turnover | Σ|trades_signal| / capital per period |
| retention | % of months with positive return |

## Minimum Viability Thresholds (v1.0)

| Criterion | Minimum |
| --- | --- |
| sample_size | > 300 signals |
| unique_symbols | ≥ 50 |
| months_coverage | ≥ 12 |
| profit_factor (IS) | > 1.4 |
| sharpe (IS) | > 1.2 |
| max_drawdown | < 25% |
| OOS degradation | PF_oos ≥ 0.7 × PF_is |

## Anti-Overfitting (mandatory steps)

1. Purged walk-forward (embargo ≥ 1 label horizon between folds).
2. OOS set used exactly once, at the end.
3. Reality check (White/Hansen) applied when candidates > 100.
4. Bootstrap CI (≥ 1000 resamples) reported for sharpe/PF.
