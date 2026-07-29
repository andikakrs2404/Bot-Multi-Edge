# SPEC-Screener

**Status:** DRAFT  
**Date:** 2026-07-27  
**Owner:** Lead Architect  

---

## Purpose

Operational contract untuk seluruh Screener pipeline. Menentukan kapasitas stage, SLA, resource budget, hardware profile, failure mode, dan KPI. Bukan arsitektur (itu ADR-003) — tapi angka pasti yang mengikat semua komponen.

## Universe Definition

```yaml
universe:
  exchanges: [BINANCE, BYBIT]
  max_symbols: 1000
  symbol_refresh_interval: 5m      # Symbol Registry polls exchange REST every 5min
  min_liquidity_filter: true       # Stage 1 fast screening removes < $1M vol
```

## Stage Capacity

| Stage | Max symbols | Notes |
|-------|-------------|-------|
| Stage 0: Metadata Layer | 1000 | All universe |
| Stage 1: Fast Screening | 300 | Filter 1000 → ~300 candidates |
| Stage 2: Feature Store | 300 | Compute features for all candidates |
| Stage 3: Normalization | 300 | Normalize all features |
| Stage 4: Market Breadth | 300 | Breadth per sector |
| Stage 5: Attention Engine | 300 | Score all candidates |
| Tier A | 20 | Hot list |
| Tier B | 50 | Watch list |
| Tier C | 200 | Scan list |
| Tier D | ∞ | Universe (periodic scan) |

## Processing Frequency

| Component | Frequency | Rationale |
|-----------|-----------|-----------|
| Market data (ticker) | Real-time (event driven) | Per tick event |
| Feature Store update | Real-time (event driven) | Compute on event |
| Fast Screening | Every 30s | Re-evaluate universe for new candidates |
| Normalization | Every feature update | ~15s cycle |
| Market Breadth | Every normalization cycle | ~15s |
| Attention Score | Every normalization cycle | ~15s |
| Tier Assignment | Every **60s** | Strict — prevents flapping |
| Focus Queue drain | Every tick (A), 5 ticks (B), 30 ticks (C) | Per ADR-009 |
| Special Situation detection | Real-time (event driven) | Independent of cycle |
| Symbol Registry refresh | Every 5 min | Exchange REST API |

## Latency Budget (SLA)

| Stage | Max latency | Measured from |
|-------|-------------|---------------|
| Market Data → Normalised Event | 500ms | Exchange WS → Event Bus |
| Feature Store compute | 100ms | Event → FeatureValue stored |
| Normalization | 50ms | Raw → percentile/rank |
| Market Breadth | 50ms | Normalized → breadth snapshot |
| Attention Engine | 50ms | Features + Breadth → score |
| Tier Assignment | 50ms | Score → Tier |
| Edge Engine (per symbol) | 50ms | Dequeue → EdgeResult |
| **Total signal path** | **1000ms** | Exchange → AggregatedSignal |

### Budget Breakdown (edge path)

Given Tier A = 20 symbols × 50ms = 1000ms worst-case for full queue drain. In practice:

| Tier | Symbols | Edges per symbol | Total eval | Budget |
|------|---------|-----------------|------------|--------|
| A | 20 | 20 | 400 | 1000ms |
| B | 10/tick | 10 | 100 | 500ms |
| C | 7/tick | 5 | 35 | 350ms |
| OQ | varies | 20 | varies | 500ms |

## Hardware Profiles

### Desktop (i3 Gen13 + GTX 1660 Ti)

```yaml
profile: desktop
max_symbols: 1000
max_tier_a: 30
max_tier_b: 50
max_tier_c: 200
edge_budget: full
feature_cache: all
breadth_enabled: true
```

### Jetson Nano 2GB

```yaml
profile: jetson_nano_2gb
max_symbols: 300
max_tier_a: 15
max_tier_b: 25
max_tier_c: 100
edge_budget: lightweight_only    # only high-priority + lightweight edges
feature_cache: partial           # only Tier A+B features cached in memory
breadth_enabled: true            # breadth still useful at 300 symbols
```

### Low-Cost VPS (2 vCPU, 4GB RAM)

```yaml
profile: vps_low
max_symbols: 500
max_tier_a: 10
max_tier_b: 20
max_tier_c: 100
edge_budget: high_priority_only
feature_cache: tier_ab_only
breadth_enabled: false           # disable breadth, use global simple metrics
```

## Resource Budget

Approximate CPU allocation per component (desktop profile, full universe):

| Component | CPU % | Notes |
|-----------|-------|-------|
| Market Data (WS + normalization) | 20% | 2 exchanges, 1000 symbols, real-time |
| Feature Store | 20% | 6 features × 300 symbols per cycle |
| Normalization + Breadth | 5% | Lightweight math |
| Attention Engine | 5% | Weighted sum, cheap |
| Tier Assignment | 2% | Sort + capacity check |
| Edge Engine | 40% | All edges on Tier A, high-priority on B, light on C |
| Miscellaneous (health, metrics, API) | 8% | |

**Memory estimate:** ~500MB for 1000 symbols × SymbolState with full features + normalized + breadth + attention.

## Degradation Modes

When system resources are constrained, degrade in this order:

| Order | Degradation | Trigger | Recover |
|-------|-------------|---------|--------|
| 1 | Disable experimental edges | CPU > 80% | CPU < 60% for 30s |
| 2 | Reduce Tier C edge budget to minimum | CPU > 85% | CPU < 65% |
| 3 | Reduce Tier A max to 10 | CPU > 90% | CPU < 70% |
| 4 | Skip breadth computation | CPU > 92% | CPU < 75% |
| 5 | Reduce universe to 500 symbols | Memory > 80% | Memory < 60% |
| 6 | Pause fast screening (keep current candidates) | CPU > 95% | CPU < 80% |

All degradations log and emit `system_degraded` event. Auto-recover when trigger clears.

## KPI (Key Performance Indicators)

| KPI | Target | Measured by |
|-----|--------|-------------|
| Symbols tracked | 1000 | Symbol count |
| Stage 1 pass rate | 25-35% | 250-350 of 1000 pass fast screen |
| Attention hit rate | 10-20% | Symbols with heat > 70 / total |
| Opportunity Queue hit rate | 1-5 / day | Special situations triggered |
| Edge signal rate | 5-15 / day | EdgeResult with direction ≠ NEUTRAL |
| Signal aggregator output | 2-5 / day | AggregatedSignal sent to execution |
| Avg signal latency | < 1000ms | Exchange event → AggregatedSignal |
| False positive rate | < 30% | Signals that triggered trade then reversed < 1h |

### Daily Operational Target

```yaml
daily_target:
  raw_signals: 5-15              # EdgeResults with direction ≠ NEUTRAL
  qualified_signals: 2-5         # AggregatedSignals passing confidence threshold
  executed_trades: 2-3           # Trades actually placed (by execution layer)
  max_daily_loss: -5%            # Hard stop per day
```

## Failure Handling

| Failure | Behavior |
|---------|----------|
| Exchange WS disconnect | Isolated per exchange. Other exchange continues. Reconnect with backoff |
| Feature Store stale | Edge Engine skips symbols with EXPIRED features |
| Breadth unavailable | Attention Engine uses neutral bias (no sector boost) |
| Single edge crash | Error isolation — other edges continue. Log error |
| Tier Assignment timeout | Use previous tier snapshot |
| Opportunity Queue overflow | Evict lowest-urgency entry (per ADR-009) |

## Dependencies

| Component | Depends on | Failure impact |
|-----------|------------|----------------|
| Feature Store | Event Bus | No feature = no edge eval |
| Normalization | Feature Store | No normalized = no attention |
| Breadth | Normalization | No breadth = neutral attention bias |
| Attention | Normalization + Breadth | No attention = default Tier D |
| Tier Assignment | Attention | No tier = previous tier snapshot |
| Edge Engine | Focus Queue | No edge = no signals |
| Signal Aggregator | Edge Engine | No aggregation = no output |

## References

- ADR-003: Screener Architecture
- ADR-009: Focus Queue
- ADR-010: Edge Framework
- SPEC-Symbol-State
