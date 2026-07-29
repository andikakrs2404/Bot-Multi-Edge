# SPEC-Research-Lifecycle

**Status:** DRAFT  
**Date:** 2026-07-27  
**Owner:** Lead Architect  

---

## Purpose

Menentukan lifecycle seluruh research artifact — Feature, Edge, Special Situation, Attention Rule — dari ide hingga production. Mencegah repo berubah menjadi tumpukan F001..F127 dan E001..E089 tanpa jelas mana yang masih menghasilkan uang.

## Universal Lifecycle

```
IDEA ──► HYPOTHESIS ──► RESEARCH ──► BACKTEST ──► PAPER_VALIDATED ──► FORWARD_TEST ──► CERTIFIED ──► PRODUCTION ──► MONITORING ──► DEPRECATED
```

| Phase | Description | Gate to pass |
|-------|-------------|--------------|
| IDEA | Concept noted. No artifact required | — |
| HYPOTHESIS | Written hypothesis with expected outcome | Document exists |
| RESEARCH | Data exploration, preliminary validation | Notebook/shared analysis |
| BACKTEST | Historical simulation | Min sample size met |
| PAPER_VALIDATED | Backtest results reviewed, no red flags | Improvement > min threshold |
| FORWARD_TEST | Live signals logged, not traded | Min signal count, no degradation |
| CERTIFIED | Full production | All gates passed + committee approval |
| PRODUCTION | Live in stack | Edge executed / Feature consumed |
| MONITORING | Regular performance review | Review cycle not expired |
| DEPRECATED | Removed from production | Kill criteria met or replaced |

## Research Artifact

Setiap ide penelitian wajib memiliki artifact:

```yaml
id: R001
type: FEATURE                    # FEATURE | EDGE | SPECIAL_SITUATION | ATTENTION_RULE
title: OI Expansion Edge
author: Lead Architect
created_at: 2026-07-27
status: HYPOTHESIS               # Current phase
related_artifacts:               # Links to Registry entries once promoted
  registry_id: null              # E001, F002, SS001 — set when CERTIFIED
```

Tanpa artifact, ide tidak boleh lanjut ke coding.

## Hypothesis Template

```yaml
hypothesis:
  statement: >
    OI expansion > P90 combined with volume > P85
    predicts above-average 1h forward returns.

  expected_improvement_pct: 15
  validation_period_days: 365
  min_sample_size: 1000
  markets: [BYBIT, BINANCE]
  symbols_min: 300
```

Setiap hypothesis wajib menjawab:
- **What** are we testing?
- **Why** should it work? (logic/market mechanic)
- **Expected improvement** over baseline?
- **How** will we measure success?

## Validation Gates

### Gate 1: BACKTEST → PAPER_VALIDATED

```yaml
gates:
  backtest:
    min_sample_size: 1000
    min_history_days: 180
    min_improvement_pct: 10
    max_drawdown_pct: 20
    profit_factor_min: 1.2
    must_pass_walk_forward: true
```

### Gate 2: PAPER_VALIDATED → FORWARD_TEST

```yaml
gates:
  forward_test:
    duration_days: 30
    min_live_signals: 100
    max_degradation_vs_backtest_pct: 20
    must_match_direction: true        # LONG signals in backtest = LONG in live
```

### Gate 3: FORWARD_TEST → CERTIFIED

```yaml
gates:
  certification:
    sample_backtest: passed
    sample_live: passed               # min_live_signals >= 100
    overfit_checked: true             # walk-forward analysis done
    degradation_within_limit: true    # < 20% degradation
    confidence_score: >= 70
    committee_approved: true
```

### Gate 4: CERTIFIED → PRODUCTION

```yaml
gates:
  production:
    registry_updated: true            # FEATURE-Registry or EDGE-Registry updated
    certification_doc_complete: true  # Full certification document exists
    monitoring_alerts_configured: true
```

## Overfit Prevention

Wajib sebelum CERTIFIED:

| Check | Method | Pass criteria |
|-------|--------|---------------|
| Walk-forward analysis | Train/test split by time | < 30% degradation |
| Out-of-sample test | Holdout 20% symbols | Same direction |
| Cross-exchange validation | Train on BYBIT, test on BINANCE | Same direction |
| Min symbol count | Not just BTC/ETH | At least 50 symbols |
| Robustness check | Perturb thresholds ±10% | < 20% signal drop |

## Forward Test Requirement

Forward test adalah **wajib**, bukan opsional. Backtest bagus belum berarti valid.

```python
@dataclass
class ForwardTestResult:
    artifact_id: str
    status: Literal["IN_PROGRESS", "PASSED", "FAILED"]
    start_date: datetime
    duration_days: int
    signal_count: int
    win_rate_live: float
    win_rate_backtest: float
    degradation_pct: float
    passed: bool
```

If `degradation_pct > 20%`: artifact auto-reverts to PAPER_VALIDATED. Must re-test with adjusted parameters.

## Certification Committee

Walaupun hanya satu orang, ada checklist formal:

```yaml
certification_checklist:
  feature_validated: true
  overfit_checked: true
  walk_forward_passed: true
  cross_exchange_consistent: true
  forward_test_passed: true
  documentation_complete: true
  confidence_score: 92
  approved: true
  approved_at: 2026-09-01
```

No self-approval shortcut. Checklist harus diisi lengkap.

## Automatic Revalidation

Crypto berubah cepat. Artifact yang tidak direview = tidak dipercaya.

| Artifact type | Review cycle | Auto-revert after |
|---------------|--------------|-------------------|
| FEATURE | 90 days | 100 days → REVIEW_REQUIRED |
| EDGE | 60 days | 75 days → REVIEW_REQUIRED |
| SPECIAL_SITUATION | 90 days | 100 days → REVIEW_REQUIRED |
| ATTENTION_RULE | 90 days | 100 days → REVIEW_REQUIRED |

Status after auto-revert: `REVIEW_REQUIRED`. Artifact still in production pending review, but flagged in dashboard.

## Kill Criteria

| Condition | Action |
|-----------|--------|
| improvement_drop > 50% vs certification baseline | CERTIFIED → WATCHLIST |
| confidence_score < 60 | CERTIFIED → WATCHLIST |
| signal_count < 50 in 30 days (edge) | CERTIFIED → WATCHLIST |
| win_rate < 45% over 60 days | WATCHLIST → DEPRECATED |
| profit_factor < 1.0 over 60 days | Immediate DEPRECATED |
| New version supersedes | Old version → DEPRECATED |

### Kill Switch Auto-Execute

```yaml
kill_switch:
  enabled: true
  auto_deprecate: true            # Automatically set DEPRECATED in registry
  notify_before: true              # Notify 24h before auto-execute
  manual_override_possible: true   # User can override with reason
```

## Alpha Attribution

Setiap trade harus bisa ditelusuri ke artifact yang menghasilkannya.

```json
{
  "trade": {
    "symbol": "BTCUSDT",
    "direction": "LONG",
    "entry_time": "2026-07-27T12:01:00Z",
    "triggered_by_edge": ["E001", "E003"],
    "situation": "SS002",
    "supporting_features": ["F002", "F003", "F004"],
    "attention_score": 92,
    "tier": "A"
  }
}
```

Dengan ini, analisis profitabilitas bisa:

```
Top profit sources:
  E001: +12.3%
  E003: +8.7%
  SS002: +15.1%   (situasi itu sendiri, bukan edge)
  F002: high correlation with winning trades
```

## Research Metrics Dashboard

| Metric | Description |
|--------|-------------|
| `active_research_count` | Total artifacts in non-DEPRECATED status |
| `certified_features` | Features at CERTIFIED or PRODUCTION |
| `certified_edges` | Edges at CERTIFIED or PRODUCTION |
| `deprecated_count` | Artifacts marked DEPRECATED |
| `avg_validation_days` | Average days from HYPOTHESIS to CERTIFIED |
| `alpha_decay_rate` | % of certified artifacts that degraded within 90 days |
| `forward_test_pass_rate` | % of forward tests that passed |

## Research Folder Structure

```
docs/research/
├── FEATURE-Registry.md
├── FEATURE-Certification.md
├── EDGE-Registry.md
├── EDGE-Certification.md
├── SPEC-Research-Lifecycle.md
│
├── hypotheses/                  # One file per hypothesis
│   ├── HYP-001-OI-Expansion.md
│   ├── HYP-002-Leader-Follower.md
│   └── ...
│
├── validations/                 # One file per validation result
│   ├── VAL-001-OI-Expansion.md
│   ├── VAL-002-Leader-Follower.md
│   └── ...
│
└── deprecated/                  # Moved here when DEPRECATED
    ├── OLD-Mean-Reversion.md
    └── ...
```

## References

- FEATURE-Certification.md
- EDGE-Certification.md
- SPEC-Screener (KPI section)
