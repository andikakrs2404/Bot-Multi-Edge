# FEATURE-Registry

**Status:** DRAFT  
**Last Updated:** 2026-07-27  
**Owner:** Lead Architect  

---

## Registry Structure

Feature registry adalah source of truth untuk semua feature. Setiap feature memiliki kontrak yang divalidasi oleh Feature Store saat startup (see ADR-004).

```yaml
feature_id: F002
feature_version: 1
name: OI Expansion
category: liquidity
owner: FeatureHandler
source_events: [open_interest]
depends_on: []
update_policy: on_event
freshness_ttl_sec: 30
research_status: CERTIFIED
```

---

## Feature Index

| ID | Name | Category | Status | Version |
|----|------|----------|--------|---------|
| F001 | Liquidity | Liquidity | CERTIFIED | 1 |
| F002 | OI Expansion | Liquidity | CERTIFIED | 1 |
| F003 | Volume Expansion | Momentum | CERTIFIED | 1 |
| F004 | RS (Relative Strength) | Momentum | CERTIFIED | 1 |
| F005 | Compression | Volatility | TESTING | 1 |
| F006 | Funding Rate | Funding | CERTIFIED | 1 |

---

## Feature Details

### F001 — Liquidity

```yaml
feature_id: F001
feature_version: 1
name: Liquidity
category: liquidity
owner: FeatureHandler
formula: volume_24h * price
raw_unit: USD
source_events: [ticker]
depends_on: []
update_policy: on_event
freshness_ttl_sec: 10
research_status: CERTIFIED
confidence_score: 95
validation_method: Cross-check with exchange reported 24h volume
expected_range: [1e6, 1e11]
```

**Purpose:** Filter low-activity symbols. Floor threshold for Stage 1 Fast Screening.

---

### F002 — OI Expansion

```yaml
feature_id: F002
feature_version: 1
name: OI Expansion
category: liquidity
owner: FeatureHandler
formula: (OI - OI_prev) / OI_prev * 100
raw_unit: percent
source_events: [open_interest]
depends_on: []
update_policy: on_event
freshness_ttl_sec: 30
research_status: CERTIFIED
confidence_score: 90
validation_method: Compare to 1h rolling OI average. Spike > 3σ flags for review.
expected_range: [-50, 50]
benchmark_source: Bybit / Binance OI history 2025-2026
```

**Purpose:** Detect capital inflow/outflow. High OI expansion = smart money positioning.

**Used by:** Attention Engine, Funding Reversal edge, OI Momentum edge.

---

### F003 — Volume Expansion

```yaml
feature_id: F003
feature_version: 1
name: Volume Expansion
category: momentum
owner: FeatureHandler
formula: (volume - vol_avg_1h) / vol_avg_1h * 100
raw_unit: percent
source_events: [candle_1m]
depends_on: []
update_policy: interval_1m
freshness_ttl_sec: 60
research_status: CERTIFIED
confidence_score: 85
validation_method: Compare to 24h volume profile. Sudden spike vs gradual buildup both valid.
expected_range: [-80, 500]
benchmark_source: Bybit / Binance volume history 2025-2026
```

**Purpose:** Detect abnormal volume — breakout, breakdown, accumulation.

**Used by:** Attention Engine, Volume Breakout edge.

---

### F004 — RS (Relative Strength)

```yaml
feature_id: F004
feature_version: 1
name: RS (Relative Strength)
category: momentum
owner: FeatureHandler
formula: price / price_avg_1h
raw_unit: ratio
source_events: [candle_1m]
depends_on: []
update_policy: interval_1m
freshness_ttl_sec: 60
research_status: CERTIFIED
confidence_score: 90
validation_method: Compare to RS against universe average. RS > 1 = outperforming.
expected_range: [0.8, 1.2]
benchmark_source: Universe median RS 2025-2026
```

**Purpose:** Relative strength vs short-term average. Core input for Market Breadth.

**Used by:** Market Breadth Engine, Attention Engine, Momentum edge, Trend Following edge.

---

### F005 — Compression

```yaml
feature_id: F005
feature_version: 1
name: Compression
category: volatility
owner: FeatureHandler
formula: (ATR_15m / price) * 100
raw_unit: percent
source_events: [candle_15m]
depends_on: []
update_policy: interval_15m
freshness_ttl_sec: 300
research_status: TESTING
confidence_score: 70
validation_method: Compare to rolling 30d ATR percentile. Bollinger band width alternative.
expected_range: [0.1, 5.0]
benchmark_source: Universe ATR percentiles 2025-2026
```

**Purpose:** Detect volatility contraction — often precedes expansion. Low compression = breakout setup.

**Used by:** Attention Engine (volatility regime bias), Compression Breakout edge.

---

### F006 — Funding Rate

```yaml
feature_id: F006
feature_version: 1
name: Funding Rate
category: funding
owner: FeatureHandler
formula: exchange_funding_rate (raw)
raw_unit: decimal
source_events: [funding]
depends_on: []
update_policy: on_event
freshness_ttl_sec: 300
research_status: CERTIFIED
confidence_score: 95
validation_method: Cross-exchange funding comparison. Extreme values > 0.1% flagged.
expected_range: [-0.01, 0.01]
benchmark_source: Bybit / Binance funding history
```

**Purpose:** Cost of carry and market sentiment. High positive = longs paying = potential squeeze/reversal.

**Used by:** Attention Engine, Special Situation Pipeline (Funding Extreme), Funding Reversal edge.

---

---

## Feature Categories

| Category | Description | Features |
|----------|-------------|----------|
| **Liquidity** | Market depth, capital flow | F001, F002 |
| **Momentum** | Directional strength | F003, F004 |
| **Volatility** | Regime detection | F005 |
| **Funding** | Cost of carry | F006 |

---

## Status Lifecycle

```
DRAFT ──► TESTING ──► CERTIFIED ──► DEPRECATED
              │            │
              ▼            ▼
         Not used in    Used in production
         edge signals   edge + attention
```

| Status | Meaning | Consumer behavior |
|--------|---------|-------------------|
| DRAFT | Being designed | Not registered in Feature Store |
| TESTING | Computed but experimental | Logged, not used in signal generation |
| CERTIFIED | Validated | Full use in attention + edge |
| DEPRECATED | Slated for removal | No new edges may depend. Existing edges migrated. |

---

## Adding a New Feature

1. Add entry to this registry with DRAFT status
2. Create Feature Handler implementing contract
3. Set TESTING — validate output vs expected range
4. Run certification tests (see FEATURE-Certification.md)
5. Set CERTIFIED — feature live in production

---

## References

- ADR-004: Feature Store
- ADR-003: Screener Architecture
- FEATURE-Certification.md
