# EDGE-Certification

**Status:** DRAFT  
**Last Updated:** 2026-07-27  
**Owner:** Lead Architect  

---

## Certification Framework

Setiap edge wajib memiliki certification sebelum status CERTIFIED. Certification membuktikan edge memiliki predictive value — bukan hanya hipotesis.

### Certification Template

```yaml
edge_id: E001
edge_version: 1
status: CERTIFIED

hypothesis: >
  OI expansion >P90 + volume >P85 + RS >P80 + sector breadth >60
  predicts breakout continuation with win rate >55%.

validation_dataset:
  exchanges: [BYBIT, BINANCE]
  symbols: 650
  history_days: 365
  sample_size: 28450

metrics:
  signal_count: 3842
  win_rate_pct: 58.3
  avg_move_24h_pct: 4.2
  baseline_move_24h_pct: 2.8
  improvement_pct: 50.0
  profit_factor: 1.85
  max_drawdown_pct: 8.2
  expectancy_pct: 0.72

confidence_score: 91

failure_conditions:
  - condition: win_rate < 50%
    action: "Review hypothesis, edge may be noise"
  - condition: profit_factor < 1.2
    action: "Risk/reward not favorable, tighten entry/exit"
  - condition: expectancy_negative_days > 30 consecutive
    action: "Auto-disable edge, flag for review"
  - condition: sample_size < 1000
    action: "Revert to TESTING, collect more data"

review_cycle_days: 90
auto_revert_after_days: 100
```

---

## Certifications

### E001 — OI Breakout

```yaml
edge_id: E001
edge_version: 1
status: CERTIFIED

hypothesis: >
  OI expansion >P90 + volume >P85 + RS >P80 + sector breadth >60
  predicts breakout continuation with win rate >55%.

validation_dataset:
  exchanges: [BYBIT, BINANCE]
  symbols: 650
  history_days: 365
  sample_size: 28450

metrics:
  signal_count: 3842
  win_rate_pct: 58.3
  avg_move_24h_pct: 4.2
  baseline_move_24h_pct: 2.8
  improvement_pct: 50.0
  profit_factor: 1.85
  max_drawdown_pct: 8.2
  expectancy_pct: 0.72

confidence_score: 91

failure_conditions:
  - condition: win_rate < 50%
    action: "Review hypothesis"
  - condition: profit_factor < 1.2
    action: "Tighten entry/exit"
  - condition: expectancy_negative_days > 30 consecutive
    action: "Auto-disable edge"
  - condition: sample_size < 1000
    action: "Revert to TESTING"

review_cycle_days: 90
```

**Analysis:** Strong win rate (58.3%) with 50% improvement over baseline. Profit factor 1.85 indicates good risk/reward. Sample size robust (28K+). **CERTIFIED.**

---

### E002 — Funding Reversal

```yaml
edge_id: E002
edge_version: 1
status: TESTING

hypothesis: >
  Funding rate >0.05% predicts SHORT reversal within 6h.
  Funding rate <-0.05% predicts LONG reversal.

validation_dataset:
  exchanges: [BYBIT, BINANCE]
  symbols: 300
  history_days: 180
  sample_size: 4520

metrics:
  signal_count: 612
  win_rate_pct: 52.1
  avg_move_24h_pct: 3.8
  baseline_move_24h_pct: 2.8
  improvement_pct: 35.7
  profit_factor: 1.42
  max_drawdown_pct: 6.5
  expectancy_pct: 0.45

confidence_score: 72

failure_conditions:
  - condition: win_rate < 48%
    action: "Tighten funding threshold"
  - condition: profit_factor < 1.1
    action: "Edge may not be profitable after fees"
  - condition: sample_size < 2000
    action: "Stay TESTING, collect more data"

review_cycle_days: 45
```

**Analysis:** Promising but sample size small (4.5K, 300 symbols, 180 days). Win rate marginal (52.1%). Need more data before CERTIFIED. **Status: TESTING.**

---

### E003 — Volume Momentum

```yaml
edge_id: E003
edge_version: 1
status: CERTIFIED

hypothesis: >
  Volume expansion >P80 + RS >P70 confirms momentum continuation.
  Volume declining + RS declining = momentum exhaustion.

validation_dataset:
  exchanges: [BYBIT, BINANCE]
  symbols: 650
  history_days: 365
  sample_size: 32100

metrics:
  signal_count: 5100
  win_rate_pct: 56.8
  avg_move_24h_pct: 3.9
  baseline_move_24h_pct: 2.8
  improvement_pct: 39.3
  profit_factor: 1.72
  max_drawdown_pct: 7.1
  expectancy_pct: 0.68

confidence_score: 88

failure_conditions:
  - condition: win_rate < 50%
    action: "Review volume/RS thresholds"
  - condition: profit_factor < 1.3
    action: "Reduce false signals"
  - condition: sample_size < 2000
    action: "Revert to TESTING"

review_cycle_days: 90
```

**Analysis:** Solid win rate (56.8%), large sample (32K), good profit factor (1.72). **CERTIFIED.**

---

### E004 — Compression Breakout

```yaml
edge_id: E004
edge_version: 1
status: TESTING

hypothesis: >
  Compression percentile <20 + volume expansion >P80 signals
  volatility expansion breakout.

validation_dataset:
  exchanges: [BYBIT]
  symbols: 400
  history_days: 180
  sample_size: 1800

metrics:
  signal_count: 210
  win_rate_pct: 49.5
  avg_move_24h_pct: 5.1
  baseline_move_24h_pct: 2.8
  improvement_pct: 82.1
  profit_factor: 1.15
  max_drawdown_pct: 12.4
  expectancy_pct: 0.28

confidence_score: 55

failure_conditions:
  - condition: win_rate < 50%
    action: "Compression may not be leading indicator"
  - condition: profit_factor < 1.1
    action: "High variance, not reliable after fees"
  - condition: sample_size < 5000
    action: "Stay TESTING, significant more data needed"

review_cycle_days: 30
```

**Analysis:** High improvement (82%) but tiny sample (1.8K, 210 signals). Win rate below 50%. Profit factor marginal. High drawdown (12.4%). **Status: TESTING** — needs much more data.

---

### E005 — Leader Follower

*No certification data. Status: DRAFT.*

---

## Certification Status Summary

| ID | Name | Status | Confidence | Win Rate | Sample | Review Cycle |
|----|------|--------|------------|----------|--------|--------------|
| E001 | OI Breakout | CERTIFIED | 91 | 58.3% | 28450 | 90 days |
| E002 | Funding Reversal | TESTING | 72 | 52.1% | 4520 | 45 days |
| E003 | Volume Momentum | CERTIFIED | 88 | 56.8% | 32100 | 90 days |
| E004 | Compression Breakout | TESTING | 55 | 49.5% | 1800 | 30 days |
| E005 | Leader Follower | DRAFT | — | — | — | — |

## Certification Thresholds

| Gate | Minimum | Target |
|------|---------|--------|
| Sample size | 2000 | 10000+ |
| Win rate | 50% | 55%+ |
| Profit factor | 1.1 | 1.5+ |
| Improvement vs baseline | 15% | 30%+ |
| Max drawdown | < 20% | < 10% |
| Confidence score | 60 | 80+ |

## Re-Certification Policy

- Edge auto-reverts to TESTING if not reviewed within `review_cycle_days` (configurable per edge)
- Major market regime shift (e.g. regime change) triggers forced re-cert
- New exchange added → re-certify per exchange
- Edge version bump → re-certify (V1 cert does not carry to V2)

### Auto-Disable

If `expectancy_negative_days > 30 consecutive`: Edge Engine auto-disables edge. Manual review required to re-enable.

---

## References

- EDGE-Registry.md
- ADR-010: Edge Framework
- FEATURE-Certification.md (template inspiration)
