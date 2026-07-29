# FEATURE-Certification

**Status:** DRAFT  
**Last Updated:** 2026-07-27  
**Owner:** Lead Architect  

---

## Certification Framework

Setiap feature wajib memiliki certification document sebelum status CERTIFIED. Certification adalah bukti bahwa feature memiliki predictive value, bukan hanya intuisi.

### Certification Template

```yaml
feature_id: F002
feature_version: 1
status: CERTIFIED
owner: Research Team
last_reviewed: 2026-07-27

hypothesis: >
  Increasing open interest while price remains stable
  indicates position accumulation and predicts larger future move.

validation_dataset:
  exchanges: [BYBIT]
  symbols: 660
  history_days: 365

validation_result:
  baseline_forward_move_pct: 13.2
  feature_forward_move_pct: 17.3
  improvement_pct: 30.8

confidence_score: 95
sample_size: 39863

failure_conditions:
  - condition: sample_size < 500
    action: "Revert to TESTING, collect more data"
  - condition: improvement_pct < 5
    action: "Review hypothesis, feature may be noise"
  - condition: walk_forward_degradation > 20
    action: "Feature overfit to historical regime, retrain threshold"
```

---

## Certifications

### F001 — Liquidity

```yaml
feature_id: F001
feature_version: 1
status: CERTIFIED
owner: Research Team
last_reviewed: 2026-07-27

hypothesis: >
  Symbols with above-median 24h liquidity exhibit lower spread,
  more reliable orderbook, and stronger technical signal persistence.
  Removal of low-liquidity symbols improves signal/noise ratio in
  all downstream edges.

validation_dataset:
  exchanges: [BYBIT, BINANCE]
  symbols: 850
  history_days: 180

validation_result:
  metric: "False signal rate below liquidity floor"
  baseline_false_signal_rate_pct: 18.5  # all symbols
  feature_false_signal_rate_pct: 7.2     # above liquidity floor
  improvement_pct: 61.1

confidence_score: 95
sample_size: 153000

note: >
  Not a predictive feature. Gate/filter. Certification confirms
  that removing low-liquidity symbols improves edge performance
  across all strategies. Used as Stage 1 Fast Screening filter.

failure_conditions:
  - condition: false_signal_rate_improvement < 20%
    action: "Lower liquidity floor threshold"
  - condition: Filter removes > 80% of universe
    action: "Only extreme outliers should be removed"
```

---

### F002 — OI Expansion

```yaml
feature_id: F002
feature_version: 1
status: CERTIFIED
owner: Research Team
last_reviewed: 2026-07-27

hypothesis: >
  Increasing open interest while price remains stable or rises
  indicates position accumulation. Decreasing OI while price rises
  indicates distribution. OI expansion predicts sustained moves;
  OI contraction predicts reversals.

validation_dataset:
  exchanges: [BYBIT]
  symbols: 660
  history_days: 365

validation_result:
  baseline_forward_move_pct: 13.2   # random symbol average 1h forward
  feature_forward_move_pct: 17.3    # symbols with OI > P80
  improvement_pct: 30.8

confidence_score: 90
sample_size: 39863

expected_range: [-50, 50]
benchmark_source: Bybit OI history 2025-2026

failure_conditions:
  - condition: sample_size < 500
    action: "Revert to TESTING, collect more data"
  - condition: improvement_pct < 5
    action: "Review hypothesis, feature may be noise"
  - condition: walk_forward_degradation > 20%
    action: "Feature overfit to historical regime, retrain thresholds"
```

---

### F003 — Volume Expansion

```yaml
feature_id: F003
feature_version: 1
status: CERTIFIED
owner: Research Team
last_reviewed: 2026-07-27

hypothesis: >
  Volume expansion relative to 1h average signals informed
  participation. High-volume breakouts more likely to sustain;
  low-volume breakouts more likely to fake out.

validation_dataset:
  exchanges: [BYBIT, BINANCE]
  symbols: 660
  history_days: 365

validation_result:
  baseline_breakout_success_rate_pct: 42.0   # all breakouts
  feature_breakout_success_rate_pct: 58.5    # volume > P80
  improvement_pct: 39.3

confidence_score: 85
sample_size: 45210

expected_range: [-80, 500]
benchmark_source: Bybit/Binance volume history 2025-2026

failure_conditions:
  - condition: sample_size < 1000
    action: "Revert to TESTING"
  - condition: improvement_pct < 10
    action: "Review volume baseline window (1h may be too short)"
  - condition: exchange divergence > 15%
    action: "Bybit vs Binance volume patterns differ — certify per exchange"
```

---

### F004 — RS (Relative Strength)

```yaml
feature_id: F004
feature_version: 1
status: CERTIFIED
owner: Research Team
last_reviewed: 2026-07-27

hypothesis: >
  Symbols with RS > 1 (price above 1h average) in the same
  sector tend to sustain outperformance. RS is a leading
  indicator for sector rotation and momentum continuation.

validation_dataset:
  exchanges: [BYBIT, BINANCE]
  symbols: 660
  history_days: 365

validation_result:
  metric: "Forward 1h return above sector median"
  baseline_sector_return_pct: 0.12       # sector average hourly return
  feature_top_quartile_return_pct: 0.31  # RS > P75 within sector
  improvement_pct: 158.0

confidence_score: 90
sample_size: 38720

expected_range: [0.8, 1.2]
benchmark_source: Universe median RS 2025-2026

failure_conditions:
  - condition: sample_size < 1000
    action: "Revert to TESTING"
  - condition: improvement_pct < 20
    action: "RS may not lead in current regime — check sector breadth correlation"
  - condition: above_ema20_breadth < 30
    action: "RS unreliable in broad distribution — reduce attention weight"
```

---

### F005 — Compression

```yaml
feature_id: F005
feature_version: 1
status: TESTING
owner: Research Team
last_reviewed: 2026-07-27

hypothesis: >
  Volatility contraction (low ATR/price percentile) often precedes
  volatility expansion. Compression identifies breakout setups
  before price moves.

validation_dataset:
  exchanges: [BYBIT]
  symbols: 400
  history_days: 180

validation_result:
  metric: "Volatility expansion within 12h after compression < P20"
  baseline_expansion_rate_pct: 18.0
  feature_expansion_rate_pct: 24.5
  improvement_pct: 36.1

confidence_score: 70
sample_size: 12500

expected_range: [0.1, 5.0]
benchmark_source: Universe ATR percentiles 2025-2026

note: >
  Still TESTING — improvement_pct promising but sample_size
  limited (400 symbols, 180 days). Expand to 660 symbols × 365 days
  before CERTIFIED. Walk-forward test pending.

failure_conditions:
  - condition: sample_size < 5000
    action: "Collect more data, stay TESTING"
  - condition: improvement_pct < 15
    action: "Compression may not predict in current low-vol regime"
  - condition: false_expansion_rate > 60%
    action: "Too many false breakouts — tighten compression percentile threshold"
```

---

### F006 — Funding Rate

```yaml
feature_id: F006
feature_version: 1
status: CERTIFIED
owner: Research Team
last_reviewed: 2026-07-27

hypothesis: >
  Extreme funding rates (> 0.05% or < -0.05%) indicate crowded
  positioning. Reversal follows as funding costs force position
  unwinding. Funding mean reversion is a reliable edge.

validation_dataset:
  exchanges: [BYBIT, BINANCE]
  symbols: 300
  history_days: 365

validation_result:
  metric: "Price reversal within 6h after funding extreme"
  baseline_reversal_rate_pct: 48.0   # random 6h window
  feature_reversal_rate_pct: 62.3    # after funding > 0.05%
  improvement_pct: 29.8

confidence_score: 95
sample_size: 28940

expected_range: [-0.01, 0.01]
benchmark_source: Bybit/Binance funding history 2025-2026

failure_conditions:
  - condition: sample_size < 1000
    action: "Revert to TESTING"
  - condition: improvement_pct < 10
    action: "Funding extreme threshold too loose — tighten to 0.08%"
  - condition: exchange divergence > 20%
    action: "Bybit vs Binance funding schedules differ — certify per exchange"
```

---

## Certification Status Summary

| ID | Feature | Status | Confidence | Sample | Last Reviewed |
|----|---------|--------|------------|--------|---------------|
| F001 | Liquidity | CERTIFIED | 95 | 153000 | 2026-07-27 |
| F002 | OI Expansion | CERTIFIED | 90 | 39863 | 2026-07-27 |
| F003 | Volume Expansion | CERTIFIED | 85 | 45210 | 2026-07-27 |
| F004 | RS | CERTIFIED | 90 | 38720 | 2026-07-27 |
| F005 | Compression | TESTING | 70 | 12500 | 2026-07-27 |
| F006 | Funding Rate | CERTIFIED | 95 | 28940 | 2026-07-27 |

## Thresholds for Certification

| Gate | Minimum | Target |
|------|---------|--------|
| Sample size | 5000 | 20000+ |
| Improvement vs baseline | 10% | 25%+ |
| Walk-forward degradation | < 30% | < 15% |
| Confidence score (subjective) | 60 | 80+ |
| Exchange coverage | 1 exchange | 2+ |

## Re-Certification Policy

- Feature auto-reverts to TESTING if not reviewed within 90 days
- Major market regime shift (e.g. spot ETF approval, China ban) triggers forced re-cert
- New exchange added → re-certify per exchange
- Feature version bump → re-certify (V1 cert does not carry to V2)

---

## References

- FEATURE-Registry.md
- ADR-004: Feature Store
