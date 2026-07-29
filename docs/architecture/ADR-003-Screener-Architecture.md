# ADR-003: Screener Architecture

**Status:** DRAFT  
**Date:** 2026-07-27  
**Author:** Lead Architect  
**Deciders:** Lead Architect  

---

## Context

Universe 500–1000 symbols, 2 exchanges, 20+ edge strategies. Tidak mungkin hitung semua feature + semua edge di setiap tick pada semua symbol. Biaya komputasi harus dibatasi dengan pipeline bertingkat yang menyaring symbol secara progresif.

Screener harus bisa:

- Scan seluruh universe dengan cost rendah
- Alokasikan resource komputasi ke symbol sinyal tinggi
- Support special situation yang bypass attention
- Replay-compatible untuk backtest

## Decision

Build **multi-stage screener** dengan progressive filtering:

```
Universe (850)
    │
    ▼
Stage 0: Metadata Layer ──► Enrich with sector, listing age, tags
    │
    ▼
Stage 1: Fast Screening ──► 250 symbols
    │
    ▼
Stage 2: Feature Store ──► Compute all features once
    │
    ▼
Stage 3: Feature Normalization ──► Raw → percentile/rank
    │
    ▼
Stage 4: Market Breadth ──► Sector & global context
    │
    ▼
Stage 5: Attention Engine ──► heat_score per symbol
    │
    ▼
Stage 6: Tier Assignment ──► A/B/C/D
    │
    ▼
Stage 7: Focus Queue ──► Ordered queue by tier
    │
    ▼
Stage 8: Edge Engine ──► 20+ edges evaluate
    │
    ▼
Signals → Execution
```

**Parallel path (bypasses Stage 1-7):**

```
Special Situation Detection ──► Opportunity Queue ──► Edge Engine
```

**Core rule:** Attention score alone must not exclude a symbol. A symbol may enter Edge Engine through **either** Focus Queue or Opportunity Queue.

## Stage Details

### Stage 0: Metadata Layer

**Goal:** Enrich every symbol with static/semi-static context before screening.

**Input:** `symbol_added` + `symbol_metadata` events from Symbol Registry (ADR-002)

**Enrichment:**

| Field | Source | Purpose |
|-------|--------|---------|
| Sector | Symbol Registry | Sector-based breadth, rotation bias |
| Listing age | Symbol Registry | Age filter, new-listing bonus |
| Market cap tier | Symbol Registry | Volatility normalization baseline |
| Tags | Symbol Registry | Edge-specific filtering (e.g. "meme" tag for sentiment edge) |

**Output:** Enriched symbol object → Stage 1.

### Stage 1: Fast Screening

**Goal:** Reduce 850 → ~250 symbols with cheap filters.

**Input:** Enriched ticker events (price, volume, OI, funding, metadata)

**Filters (cheap, O(n)):**

| Filter | Cost | Description |
|--------|------|-------------|
| Liquidity floor | O(1) | Volume 24h > $1M |
| OI floor | O(1) | OI > $500K |
| Age filter | O(1) | Listing > 24h (unless special situation) |
| Funding sanity | O(1) | Funding rate > -0.5% (filter dying coins) |
| Spread sanity | O(1) | Spread < 0.1% of price |

> **Note:** Thresholds above are examples. Production should use **configurable percentile-based thresholds** (e.g. volume > P70 of universe, OI > P60). Market changes; hardcoded $ values drift.

**Output:** Candidate list (~250 symbols) + enriched snapshot.

**SLA:** < 3 sec for full universe scan.

### Stage 2: Feature Store

**Goal:** Compute all features once for the 250 candidates.

**Input:** Candidate list from Stage 1 + raw market data

**Feature computation:** Each feature computed exactly once per symbol per update window. See ADR-004 for detail.

**Output:** `SymbolFeatureMap { symbol → { feature_id → raw_value } }`

**SLA:** < 10 sec for all 250 symbols.

### Stage 3: Feature Normalization

**Goal:** Convert raw feature values to percentile/rank so different features comparable.

**Why explicit stage:**

```
OI = 2.1%          →  OI_PCTL = 92
Volume = $5M       →  VOL_PCTL = 78
RS = 1.02          →  RS_PCTL = 65
```

Raw values meaningless in isolation. Percentile on universe (250 symbols) gives context.

**Normalization methods:**

| Method | When | Example |
|--------|------|---------|
| Percentile (universe) | Default for all features | OI_PCTL = ranking within 250 symbols |
| Z-score | Volatility features | RS_Z = (value - μ) / σ |
| Min-max | Bounded features (e.g. age) | (value - min) / (max - min) |

**Output:** `SymbolFeatureMap { symbol → { feature_id → normalized_value, rank, percentile } }`

**SLA:** < 2 sec for 250 symbols.

### Stage 4: Market Breadth

**Goal:** Compute sector and global market context for attention bias.

**Input:** Normalized features from Stage 3

**Computation per sector:**

```
breadth_sector_X = % of sector symbols with RS > 50
```

**Example output:**

```json
{
  "global": { "above_ema20_pct": 72, "avg_heat": 55 },
  "sectors": {
    "AI": { "symbol_count": 45, "above_ema20_pct": 85, "avg_heat": 68 },
    "DEX": { "symbol_count": 30, "above_ema20_pct": 40, "avg_heat": 32 },
    "MEME": { "symbol_count": 120, "above_ema20_pct": 55, "avg_heat": 48 }
  }
}
```

**How breadth affects attention:** Sector breadth > 70% = all symbols in that sector get attention bias +5. Sector breadth < 30% = bias -5 (sector in distribution, reduce exposure).

**Breadth output structure:**

```json
{
  "global_breadth": 74,
  "above_ema20_pct": 72,
  "avg_heat": 55,
  "breadth_regime": "EXPANSION",
  "sectors": {
    "AI": { "symbol_count": 45, "breadth": 88, "avg_heat": 68 },
    "DEX": { "symbol_count": 30, "breadth": 40, "avg_heat": 32 },
    "MEME": { "symbol_count": 120, "breadth": 55, "avg_heat": 48 }
  }
}
```

| Field | Description |
|-------|-------------|
| `global_breadth` | % of universe with RS > 50 |
| `breadth_regime` | EXPANSION (>70), NEUTRAL (40-70), CONTRACTION (<40) |
| `sectors[].breadth` | Same metric filtered per sector |

**SLA:** < 1 sec.

### Stage 5: Attention Engine

**Goal:** Rank 250 symbols by signal potential.

**Input:** Normalized features (Stage 3) + Market Breadth (Stage 4) + Metadata (Stage 0)

**Computation:**

```
heat_score = Σ(w_i × feature_i_normalized) + sector_breadth_bonus + metadata_bias
```

Where:
- `w_i` = configurable weight per feature (from FEATURE-Certification confidence scores)
- `sector_breadth_bonus` = +5/-5 based on sector breadth
- `metadata_bias` = listing age bonus, market cap tier adjustment

**Output:** `{ symbol → heat_score, attention_breakdown }` for all 250 symbols.

**Output event:**

```json
{
  "symbol": "BTCUSDT",
  "heat_score": 92,
  "tier": "A",
  "attention_breakdown": {
    "features": { "OI_EXPANSION": 18, "VOLUME_EXPANSION": 15, "RS": 12, "HEAT": 10 },
    "sector_bonus": 5,
    "metadata_bias": 2
  }
}
```

**SLA:** < 3 sec for 250 symbols.

### Stage 6: Tier Assignment

**Goal:** Map heat_score → discrete tier. Separated from Attention Engine because tier logic will evolve independently (promotion history, tier residency, speed of promotion).

**Tier thresholds (configurable):**

| Tier | Symbols | Heat threshold | Evaluation frequency |
|------|---------|----------------|---------------------|
| A | Top 10 | heat ≥ 80 | Every tick |
| B | 11–50 | heat ≥ 60 | Every 5 ticks |
| C | 51–250 | heat ≥ 30 | Every 30 ticks |
| D | Rest (universe) | heat < 30 | On demand / periodic scan |

**Tier boundaries not static — they adapt to market regime.** In low-volatility environment, thresholds shift down. Exact adaptation logic deferred to V2.

> **Tier transitions must be persisted** — promotion count, promotion speed (cycles to move up a tier), tier residency (consecutive cycles in same tier). Required for future attention model tuning and edge performance analysis per tier.

**SLA:** < 500ms.

### Stage 7: Focus Queue

**Goal:** Maintain ordered queue of symbols by tier for Edge Engine consumption.

**Queue structure — capacity bounds:**

| Tier | Slots | Overflow behavior |
|------|-------|-------------------|
| A | 5–20 | Newcomer displaces lowest-heat in A, demoted to B |
| B | 20–100 | Overflow spills to C |
| C | 100–300 | Overflow spills to D |
| D | ∞ (universe) | Periodic scan only |

**Properties:**
- FIFO within tier
- Tier A always processed first (strict priority)
- Tier B processed after all Tier A items consumed
- Tier C/D processed in remaining time

```
Focus Queue
  ├── Tier A (top 10)     ──► always drained first
  ├── Tier B (top 11-50)  ──► drained after A
  ├── Tier C (top 51-250) ──► drained after B
  └── Tier D (rest)       ──► drained in idle cycles
```

**Queue state persisted for replay.**

**SLA:** Update < 1 sec.

### Stage 8: Edge Engine

**Goal:** Run N edge strategies on Focus Queue + Opportunity Queue symbols.

**Input:** Focus Queue + Opportunity Queue + normalized features from Feature Store (shared, never recomputed)

**Each edge:**
- Reads features from shared store (zero recomputation)
- Applies strategy-specific logic
- Emits signal or skip

**Edge Engine processes Opportunity Queue before Focus Queue** — special situations always get first look.

## Special Situation Pipeline

**Goal:** Catch events that bypass Stage 0-7 attention. Core rule: attention score alone must not exclude a symbol.

**Events monitored:**

| Situation | Detection | Action |
|-----------|-----------|--------|
| New listing | `symbol_added` event | Immediately compute features, push to Opportunity Queue |
| Funding extreme | Funding rate > 0.1% or < -0.1% | Push symbol to Opportunity Queue |
| Liquidation cascade | 3+ liquidations on same symbol in 60s | Push to Opportunity Queue (high priority) |
| Exchange incident | `connection_status` reconnect | Flag for manual review |
| Massive OI spike | OI change > 20% in 5 min | Push to Opportunity Queue |

**Opportunity Queue:** High-priority queue feeding directly into Edge Engine. Bypasses Attention entirely. Edge Engine drains Opportunity Queue before Focus Queue.

## Promotion / Demotion Policy

### Promotion (to higher tier)

A symbol promoted when **any** condition met for 1 full tick cycle:

| Promotion | Condition |
|-----------|-----------|
| Tier D → C | Volume velocity P80+ OR OI velocity P80+ OR heat > 70 |
| Tier C → B | Heat > 70 for 2 consecutive cycles OR heat > 85 for 1 cycle |
| Tier B → A | Heat > 85 for 2 consecutive cycles OR in top 5 by heat for 1 cycle |

### Demotion (to lower tier)

| Demotion | Condition |
|----------|-----------|
| Tier A → B | Heat < 80 for 3 consecutive cycles |
| Tier B → C | Heat < 60 for 3 consecutive cycles |
| Tier C → D | Heat < 30 for 3 consecutive cycles |

### Special overrides

- **New listing:** Temporarily assigned Tier C for first 24h regardless of heat score (bypasses attention-based tiering during warmup)
- **Funding extreme detected:** Symbol promoted 1 tier for duration of extreme event
- **Liquidation cascade:** Symbol promoted to Opportunity Queue (bypasses tier system)

## Universe Lifecycle

```
Symbol Added (symbol_added event)
    │
    ▼
Metadata Enrichment (Stage 0)
    │
    ▼
Pre-screen (Stage 1)
    │
    ├── Pass? ──► Feature computation (Stage 2)
    │              │
    │              ▼
    │         Normalization → Breadth → Attention → Tier (Stages 3-6)
    │
    └── Fail? ──► Periodic re-check every 5 min (bail if dead after 4h)
```

- Symbol removed: `symbol_removed` → remove from all stages and queues (A, B, C, D, Opportunity)
- Metadata change: `symbol_metadata` → re-evaluate metadata bias, re-check age filter

## Attention Allocation Policy

> **Attention score alone must not exclude a symbol from being evaluated.**

A symbol may enter Edge Engine through two paths:

1. **Focus Queue** — via normal Attention → Tier pipeline
2. **Opportunity Queue** — via Special Situation Detection (bypasses Attention entirely)

No symbol is permanently excluded. Tier D symbols are re-evaluated every N cycles. Special situations can override any tier.

## SLA Summary

| Stage | Max Latency |
|-------|-------------|
| Stage 0: Metadata Layer | < 500ms |
| Stage 1: Fast Screening | 3 sec |
| Stage 2: Feature Store | 10 sec |
| Stage 3: Normalization | 2 sec |
| Stage 4: Market Breadth | 1 sec |
| Stage 5: Attention Engine | 3 sec |
| Stage 6: Tier Assignment | 500ms |
| Stage 7: Focus Queue update | 1 sec |
| Stage 8: Edge Engine (Tier A) | 1 sec per tick |
| Special Situation Detection | < 1 sec |

## Non-Goals (V1)

- Machine learning / adaptive attention weights
- Order execution integration
- Sector rotation engine
- Cross-exchange arbitrage detection
- Adaptive tier thresholds based on volatility regime

## Consequences

**Positive:**
- Progressive filtering bounds compute cost: 850 → 250 → 50 → 10 per cycle
- Shared Feature Store prevents N× recomputation across edges
- Special Situation Pipeline ensures high-impact events never missed despite attention gating
- Metadata + Breadth + Normalization as explicit stages makes attention explainable
- Tier Assignment separated from Attention enables independent evolution (promotion history, residency tracking)
- Each stage independently testable and replaceable
- Promotion/demotion policy prevents oscillation and ensures stability

**Negative:**
- Stage 1 filters critical — false negatives at fast screening mean symbol never reaches attention
- Attention weights (w_i) need tuning; bad weights = blind spots
- Focus Queue tier scheduling adds complexity (tick counters, promotion/demotion rules)
- Edge Engine limited to Focus Queue + Opportunity Queue size — overflow risk if too many symbols high-signal simultaneously
- Promotion/demotion thresholds may need tuning per market regime

## References

- ADR-001: System Overview
- ADR-002: Market Data Layer
- ADR-004: Feature Store
- ADR-005: Attention Allocation
- SPEC-Screener.md
- SPEC-Symbol-State.md
