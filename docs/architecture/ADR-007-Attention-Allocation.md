# ADR-007: Attention Allocation Engine

**Status:** DRAFT  
**Date:** 2026-07-27  
**Author:** Lead Architect  
**Deciders:** Lead Architect  

---

## Context

Universe 500–1000 symbols, 20+ edge strategies. Tidak mungkin evaluasi semua edge pada semua symbol setiap tick. Attention Engine adalah "CPU scheduler" — mengalokasikan resource komputasi ke symbol yang paling layak dianalisis.

Attention Engine **bukan** signal generator. Bukan entry finder. Output-nya adalah **attention_score** per symbol + **heat_score** untuk Tier Assignment.

## Decision

Build **Attention Allocation Engine** yang menghitung attention_score dari 3 input source:

```
Normalization Store (normalized features)
    +
Market Breadth (sector context, regime)
    +
Metadata Layer (listing age, sector, tags)
    │
    ▼
Attention Engine
    │
    ├──► attention_score per symbol (0-100)
    ├──► heat_score (derived)
    ├──► attention_breakdown (explainability)
    └──► promotion/demotion hints
           │
           ▼
         Attention Store  ──► Tier Assignment (ADR-008)
```

**Core rule:** Attention Engine must not suppress Special Situation candidates. Opportunity Queue (ADR-003) bypasses Attention entirely.

## Architecture

```
Normalized Features
  (OI_PCTL, VOL_PCTL, RS_PCTL, COMPRESSION_PCTL)
    │
    ▼
Breadth Context
  (sector_breadth, velocity, regime, leader_breadth)
    │
    ▼
Metadata Context
  (sector, listing_age, market_cap_tier)
    │
    ▼
Weighted Sum Calculator
  (configurable weights per source)
    │
    ▼
Attention Score
    │
    ├──► Attention Decay (exponential decay per cycle)
    ├──► Heat Score (attention_score + velocity bonus)
    └──► Explainability (top_reasons, breakdown)
           │
           ▼
Attention Store
    │
    ├──► Tier Assignment (ADR-008)
    └──► Dashboard (human readable)
```

### Components

| Component | Role |
|-----------|------|
| **Weighted Sum Calculator** | Σ(w_i × source_i) with configurable weights |
| **Attention Decay** | Exponential decay — attention drops if features fade |
| **Heat Score Derivation** | Attention_score + velocity bonus for fast-changing symbols |
| **Explainability** | Top reasons + component breakdown for every symbol |
| **Attention Store** | Read-only store of latest scores + components |

## Input

### From Normalization Store (ADR-005)

```json
{
  "symbols": [
    {
      "symbol": "TAOUSDT",
      "features": {
        "F002_OI_EXPANSION":   { "percentile_30d": 95, "normalized_score": 95 },
        "F003_VOLUME_EXPANSION": { "percentile_30d": 88, "normalized_score": 88 },
        "F004_RS":             { "percentile_30d": 91, "normalized_score": 91 },
        "F005_COMPRESSION":    { "percentile_30d": 12, "normalized_score": 12 },
        "F006_FUNDING":        { "percentile_30d": 72, "normalized_score": 72 }
      }
    }
  ]
}
```

### From Market Breadth (ADR-006)

```json
{
  "TAOUSDT": {
    "sector": "AI",
    "sector_bull_breadth": 88,
    "sector_velocity_15m": 12,
    "leader_breadth": 66,
    "breadth_regime": "EXPANSION",
    "breadth_quality": "BROAD"
  }
}
```

### From Metadata Layer

```json
{
  "sector": "AI",
  "listing_age_days": 420,
  "market_cap_tier": "large",
  "tags": ["decentralized-ai", "compute"]
}
```

## Output

### Attention Record (per symbol)

```json
{
  "symbol": "TAOUSDT",
  "exchange": "BINANCE",
  "attention_score": 87.5,
  "heat_score": 91.0,
  "attention_velocity_15m": 14.5,
  "attention_components": {
    "oi_expansion": 20,
    "volume_expansion": 15,
    "rs": 15,
    "compression": 5,
    "funding": 8,
    "sector_breadth": 14,
    "breadth_velocity": 10,
    "leader_breadth": 8,
    "metadata_bias": 2,
    "special_bonus": 0
  },
  "reason_codes": ["OI_EXPANSION", "VOLUME_EXPANSION", "AI_SECTOR_BREADTH", "LEADER_BREADTH"],
  "top_reasons": [
    "OI percentile 95",
    "Sector breadth 88 (AI)",
    "Breadth velocity +12",
    "Leader breadth 66"
  ],
  "decay_factor": 0.95,
  "sticky_duration_remaining_cycles": 12,
  "promotion_candidate": true,
  "demotion_candidate": false,
  "calculated_at": "2026-07-27T12:01:00.000Z"
}
```

### Field Definitions

| Field | Description |
|-------|-------------|
| `attention_score` | 0–100. Structural score — is this symbol interesting in general? |
| `heat_score` | 0–100. Realtime urgency — does this symbol need analysis NOW? |
| `attention_velocity_15m` | Delta of attention_score over last 15m. Fast-rising interest |
| `attention_components` | Per-source breakdown — explainability + debug |
| `reason_codes` | Machine-readable codes for dashboard/alerts/telegram filtering |
| `top_reasons` | Human-readable top 3-4 drivers |
| `decay_factor` | Exponential decay applied per cycle if no feature update |
| `sticky_duration_remaining_cycles` | Cycles remaining before symbol tolerates demotion (anti-flapping) |
| `promotion_candidate` | True if heat_score > threshold for promotion (used by ADR-008) |
| `demotion_candidate` | True if attention_score < threshold for demotion |

## Attention Formula

```
attention_score = Σ(wi × source_i) × sector_multiplier × decay_factor
```

Where:

| Source (i) | Data Origin | Default Weight (wi) | Notes |
|------------|-------------|---------------------|-------|
| **oi_expansion** | F002 percentile_30d | 20 | Capital inflow detection |
| **volume_expansion** | F003 percentile_30d | 15 | Participation confirmation |
| **rs** | F004 percentile_30d | 15 | Relative strength |
| **compression** | F005 inverse percentile_30d | 10 | Low percentile = high compression = attention |
| **funding** | F006 percentile_30d (extreme) | 5 | Only contributes when extreme (> P90 or < P10) |
| **sector_breadth** | Sector bull_breadth (÷ 100 × 15) | 15 | Sector context — strong sector boosts all members |
| **breadth_velocity** | Sector velocity_15m (normalised) | 10 | Accelerating sector = attention boost |
| **leader_breadth** | Leader breadth (÷ 100 × 5) | 5 | Large-cap health context |
| **metadata_bias** | Listing age + market cap tier | 2 | Small bonus for age/cap |
| **special_bonus** | Set externally (Special Situation) | 0 | Set to 50 when promoted via Opportunity Queue |

**sector_multiplier:** Derived from breadth regime — EXPANSION = 1.0, NEUTRAL = 0.8, CONTRACTION = 0.6, EUPHORIA = 0.7 (bias against late stage).

**Weights are configurable** — stored externally, not hardcoded. A `weights.yaml` is loaded at startup.

## Heat Score (Structural vs Urgency)

Scores have two dimensions:

| Score | Question | Use |
|-------|----------|-----|
| **attention_score** | Is this symbol interesting in general? | Sustained tier assignment |
| **heat_score** | Does this symbol need analysis NOW? | Tier promotion, urgent allocation |

```
attention_score = structural_score (what to watch)
heat_score = realtime_urgency_score (what to act on now)
```

Formula:

```
heat_bonus = min(Δattention_last_15m × 0.5, 15)
heat_score = attention_score + heat_bonus
```

| Δattention_15m | heat_bonus | Rationale |
|----------------|------------|-----------|
| +20 | +10 | Fast-improving features = rising attention |
| +10 | +5 | Moderate improvement |
| 0 | 0 | Stable |
| -10 | -5 | Declining |
| < -20 | capped at -10 | Rapidly fading |

Heat score is the primary signal for **Tier Promotion**. Attention score is primary for **sustained** tier assignment.

## Attention Decay

Without decay, a symbol that briefly spiked stays high forever.

```
decay_factor = exp(-λ × cycles_without_update)
λ = 0.05 (configurable)
```

After N idle cycles:
- 10 cycles: decay_factor = 0.61
- 20 cycles: 0.37
- 30 cycles: 0.22
- 50 cycles: 0.08

**Floor:** attention_score never drops below 5 (symbol still visible in Tier D).

On feature update: decay resets to 1.0.

## Attention Velocity

Attention velocity adalah perubahan attention_score dalam jendela 15m. Untuk futures scalping, velocity sering lebih penting daripada level absolut.

```
attention_velocity_15m = attention_score_now - attention_score_15m_ago
```

| Velocity | Meaning | Effect |
|----------|---------|--------|
| > +20 | Rapidly gaining interest | Boost heat_score, flag for urgent scan |
| +10 to +20 | Rising | Moderate heat boost |
| -10 to +10 | Stable | No velocity effect |
| -20 to -10 | Fading | Reduce heat score |
| < -20 | Rapidly losing interest | Demotion candidate |

Attention velocity stored per symbol in Attention Store — enables `attention_velocity_15m` output field.

## Sector Concentration Guard

Mencegah satu sektor memonopoli Tier A/B.

Tanpa guard: AI sector breadth 95 → TAO, RNDR, AKT, IO, FET all top-tier → Focus Queue 80% AI → sector lain terabaikan.

**Rule:**
```
max_sector_share = 30% of Tier A + B slots
```

| Sector size (active symbols) | Max slots in Tier A+B |
|------------------------------|-----------------------|
| 5 symbols | 3 |
| 10 symbols | 6 |
| 45 symbols (AI) | 15 (from 50 total) |

**Enforcement:** After attention scoring, if sector exceeds max share, lowest-score symbols in that sector are capped at Tier C entry. Score itself preserved — tier assignment uses capped visibility.

**Known limitation:** Guard may exclude a genuinely strong symbol if sector is crowded. `sector_diversity_bonus` considered as future extension.

## Sticky Duration

Anti-flapping mechanism. Symbol that just entered Tier A resists demotion for N cycles.

```
sticky_duration_cycles = 30  (~7.5 min at 15s cycle)
sticky_duration_remaining → decremented every cycle
```

While sticky: demotion_candidate blocked even if score drops.

| State | Sticky active | Can demote? |
|-------|---------------|-------------|
| Just promoted to Tier A | Yes (30 cycles) | No |
| 15 cycles in Tier A | Yes (15 remaining) | No |
| 30 cycles in Tier A | No | Yes |

Sticky also applies to Tier B → C and C → D transitions (shorter: 15 cycles for B, 5 for C).

## Leader/Follower Bias (Future Extension)

Placeholder untuk roadmap.

**Concept:** Jika leader (BTC/ETH/SOL) mendapat attention spike, follower di sektor yang sama mendapat `follower_bonus` attention.

```yaml
# future — not implemented in V1
leader_follower:
  enabled: false
  leader_basket: [BTC, ETH, SOL]
  follower_bonus_pct: 10
  propagation_delay_cycles: 5
```

Belum diimplementasikan di V1. Dicatat di ADR untuk referensi arsitektur.

## Promotion & Demotion Hints

Attention Engine outputs hints for Tier Assignment (ADR-008):

| Hint | Condition |
|------|-----------|
| `promotion_candidate` | heat_score > 70 AND rising velocity |
| `demotion_candidate` | attention_score < 30 AND no feature update for 10+ cycles |
| `sticky` | Symbol in Tier A for < 3 cycles — resists demotion (anti-flapping) |

These are hints, not commands. Tier Assignment (ADR-008) makes final decision.

## Configurable Weights

```yaml
# weights.yaml (loaded at startup, hot-reloadable)
weights:
  oi_expansion: 20
  volume_expansion: 15
  rs: 15
  compression: 10
  funding: 5
  sector_breadth: 15
  breadth_velocity: 10
  leader_breadth: 5
  metadata_bias: 2
  special_bonus: 0

decay:
  lambda: 0.05
  floor: 5

heat:
  velocity_cap: 15
  velocity_multiplier: 0.5

velocity:
  window_minutes: 15

sector_concentration:
  max_share_pct: 30
  enabled: true

sticky:
  tier_a_cycles: 30
  tier_b_cycles: 15
  tier_c_cycles: 5

leader_follower:
  enabled: false              # V2 feature
  follower_bonus_pct: 10
  propagation_delay_cycles: 5
```

## Special Situation Handling

Per ADR-003: Special Situation Pipeline bypasses Attention Engine entirely.

**Explicit rule:** Attention Engine must not suppress Special Situation candidates. Symbols in Opportunity Queue have `special_bonus = 50` in their attention record — guaranteeing high score for Tier Assignment, but the real path is Opportunity Queue → Edge Engine directly.

```yaml
flow:
  - Special Situation detected → Opportunity Queue → Edge Engine (primary path)
  - Special Situation detected → Attention Engine notified (for dashboard visibility only)
```

## Attention Explainability

Setiap attention record punya `top_reasons` (human-readable) + `attention_components` (machine-readable).

Tujuannya: ketika developer lihat "TAO attention=87", mereka bisa langsung tahu kenapa:

```
OI percentile 95
Sector breadth 88
Breadth velocity +12
```

Tanpa explainability, debugging attention = tebak-tebakan.

## Attention Store

Read-only store for consumers.

```python
# Get all scores for all active symbols
get_attention_snapshot() -> Dict[symbol, AttentionRecord]

# Get scores for specific tier
get_attention_by_tier(tier) -> Dict[symbol, AttentionRecord]

# Get attention history for one symbol (for heat velocity)
get_attention_history(symbol, minutes=30) -> List[AttentionRecord]
```

## Consumer Map

| Consumer | Reads | What |
|----------|-------|------|
| Stage 6: Tier Assignment (ADR-008) | attention_score, heat_score, hints | Assign A/B/C/D tiers |
| Dashboard UI | top_reasons, components, heat_score | Human monitoring |
| Edge Engine (optional) | attention_score | Filter: only evaluate symbols above attention floor |

## Update Frequency

| Metric | Frequency | Rationale |
|--------|-----------|-----------|
| attention_score | Every Normalization cycle (~15s) | Changes with each feature update |
| heat_score | Every cycle | Velocity needs recent history |
| decay | Every idle cycle | Prevents stale attention |

## Non-Goals (V1)

- Machine learning / learned weights
- Reinforcement learning for attention allocation
- Cross-exchange attention (symbol on Bybit vs Binance scored independently)
- Adaptive weight tuning (weights are manually configured, not auto-tuned)

## Consequences

**Positive:**
- Attention Engine bounds the primary evaluation path. Special Situation candidates may bypass attention
- Configurable weights separate between research and implementation
- Decay prevents stale symbols from hogging Tier A
- Explainability makes attention decisions debuggable (reason_codes, attention_components)
- Heat score vs attention score separation (structural vs urgency) catches both sustained and fast-moving signals
- Attention velocity enables scalping-oriented early detection
- Sector concentration guard prevents sector monopoly in Focus Queue
- Sticky duration prevents flapping — symbol gets fair evaluation window
- Leader/follower hook enables future sector rotation without refactor

**Negative:**
- Weight tuning is manual — bad weights = blind spots
- Decay may be too aggressive in slow-moving markets (features don't update = attention decays even if signal valid)
- Heat score bonus may cause flapping if velocity threshold too sensitive
- Sector concentration guard may exclude genuinely strong symbol in crowded sector
- Sticky duration adds latency to tier adjustments
- Special Situation bypass is correct but adds complexity — two paths for Edge entry

## References

- ADR-003: Screener Architecture (Stage 5: Attention Engine)
- ADR-005: Feature Normalization
- ADR-006: Market Breadth
- ADR-008: Tier Assignment
- weights.yaml
