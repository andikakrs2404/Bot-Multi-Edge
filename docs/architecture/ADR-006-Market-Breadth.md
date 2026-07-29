# ADR-006: Market Breadth

**Status:** DRAFT  
**Date:** 2026-07-27  
**Author:** Lead Architect  
**Deciders:** Lead Architect  

---

## Context

Feature Store + Normalization memberi tahu seberapa kuat **satu symbol**. Tapi sistem tidak tahu apakah itu gerakan individual atau gerakan sektor/market.

Perbedaan kritis:

```
Kasus A: TAO naik 8% sendirian  →  gerakan individual, risiko koreksi tinggi
Kasus B: TAO naik 8%, RNDR, FET, AKT, IO ikut naik  →  sektor AI breadth 88%, gerakan kuat
```

Attention Engine butuh konteks pasar untuk menentukan apakah suatu symbol layak dievaluasi.

## Decision

Build **Market Breadth Engine** yang menghitung persentase symbol sehat per sektor dan global. Breadth membaca **Normalization Store** (ADR-005) — bukan raw features.

```
Normalization Store
    │
    ▼
Market Breadth Engine
    │
    ├──► Global Breadth
    ├──► Sector Breadths (per sector)
    ├──► Bull/Bear Breadth
    ├──► Breadth Velocity
    └──► Leader Breadth
           │
           ▼
Breadth Store  ──► Attention Engine (ADR-007)
```

## Architecture

```
Normalized Features (from Normalization Store)
    │
    ▼
Sector Classifier
  (assign symbol → sector via Metadata Layer)
    │
    ▼
Breadth Calculator
  ├── Global: % of universe with RS_PCTL > 50
  ├── Sector: % of sector symbols with RS_PCTL > 50
  ├── Bull:   % with RS_PCTL > 60
  ├── Bear:   % with RS_PCTL < 40
  └── Leader: % of leader basket with RS_PCTL > 50
    │
    ▼
Velocity Calculator
  (breadth_delta_15m, breadth_delta_30m, breadth_delta_1h)
    │
    ▼
Regime Classifier
  (breadth value + velocity → regime label)
    │
    ▼
Breadth Store
    │
    ├──► Attention Engine (bias per sector)
    └──► Edge Engine (regime context)
```

### Components

| Component | Role |
|-----------|------|
| **Sector Classifier** | Maps symbol → sector from Metadata Layer. Unknown → `UNKNOWN` |
| **Breadth Calculator** | Computes % of symbols with RS_PCTL above threshold, per scope |
| **Velocity Calculator** | Delta of breadth over 15m, 30m, 1h windows |
| **Regime Classifier** | Maps breadth + velocity → CONTRACTION / NEUTRAL / EXPANSION / EUPHORIA |
| **Breadth Store** | Read-only store of latest breadth snapshot + history |

## Input

From Normalization Store:

```json
{
  "symbols": [
    {
      "symbol": "TAOUSDT",
      "exchange": "BINANCE",
      "sector": "AI",
      "rs_percentile_30d": 88,
      "volume_percentile_30d": 72,
      "oi_percentile_30d": 65,
      "normalized_at": "2026-07-27T12:00:00.100Z"
    }
  ]
}
```

Breadth primarily uses **RS percentile** (F004). Secondary: volume percentile for volume breadth.

## Output

### Breadth Snapshot

```json
{
  "snapshot_id": "br-20260727-120100",
  "timestamp": "2026-07-27T12:01:00.000Z",
  "global_breadth": 74,
  "global_volume_breadth": 68,
  "breadth_regime": "EXPANSION",
  "sectors": {
    "AI": {
      "symbol_count": 45,
      "bull_breadth": 88,
      "bear_breadth": 5,
      "volume_breadth": 82,
      "velocity_15m": 12,
      "velocity_30m": 8,
      "velocity_1h": -3
    },
    "MEME": {
      "symbol_count": 120,
      "bull_breadth": 42,
      "bear_breadth": 32,
      "volume_breadth": 38,
      "velocity_15m": -5,
      "velocity_30m": -15,
      "velocity_1h": -22
    },
    "DEFI": {
      "symbol_count": 80,
      "bull_breadth": 65,
      "bear_breadth": 18,
      "volume_breadth": 60,
      "velocity_15m": 3,
      "velocity_30m": 5,
      "velocity_1h": 2
    }
  },
  "leaders": {
    "BTC": { "rs_percentile": 75, "breadth_contribution": "positive" },
    "ETH": { "rs_percentile": 62, "breadth_contribution": "neutral" },
    "SOL": { "rs_percentile": 88, "breadth_contribution": "positive" }
  },
  "breadth_regime": "EXPANSION",
  "breadth_quality": "BROAD"
}
```

### Field Definitions

| Field | Description |
|-------|-------------|
| `global_breadth` | % of all Stage-2 symbols with RS percentile > 50 |
| `global_volume_breadth` | % with volume percentile > 50 |
| `breadth_regime` | CONTRACTION / NEUTRAL / EXPANSION / EUPHORIA |
| `breadth_quality` | BROAD (many sectors green) / NARROW (few sectors) / DIVERGENT (sectors split) |
| `sectors[].bull_breadth` | % with RS percentile > 60 (healthy uptrend) |
| `sectors[].bear_breadth` | % with RS percentile < 40 (downtrend) |
| `sectors[].velocity_15m` | Delta breadth over last 15 minutes |
| `leaders[]` | Key large-cap symbols and their breadth signal |
| `breadth_quality` | Pattern classification for quick consumption |

## Breadth Regimes

| Regime | Global Breadth | Velocity | Attention bias | Edge behavior |
|--------|---------------|----------|---------------|---------------|
| **EUPHORIA** | > 80 | Positive or flat | Reduce weight — late stage | Take profit, tighten stops |
| **EXPANSION** | 60–80 | Positive | Full attention | Trend edges active |
| **NEUTRAL** | 40–60 | Flat | Normal | Selective, mean-reversion edges |
| **CONTRACTION** | < 40 | Negative | Caution — focus on resilient sectors | Short edges, mean-reversion |

**Transition rules:**

```
CONTRACTION ──► NEUTRAL     when breadth > 40 for 2 consecutive readings
NEUTRAL     ──► EXPANSION   when breadth > 60 for 2 consecutive readings
EXPANSION   ──► EUPHORIA    when breadth > 80
EUPHORIA    ──► NEUTRAL     when breadth drops below 70 (skip CONTRACTION — soft landing)
NEUTRAL     ──► CONTRACTION when breadth < 40 for 2 consecutive readings
```

## Bull vs Bear Breadth

Instead of single percentage, Breadth Engine computes two axes per sector:

```
bull_breadth = % of sector symbols with RS_PCTL > 60
bear_breadth = % of sector symbols with RS_PCTL < 40
```

These are not complements — a sector can have 60% bull + 20% bear (20% neutral = consolidating).

| Pattern | Bull | Bear | Signal |
|---------|------|------|--------|
| Broad uptrend | > 70 | < 10 | Strong momentum |
| Mixed | 30–60 | 20–40 | Selective, stock-picking environment |
| Broad downtrend | < 10 | > 70 | Avoid sector entirely |
| Divergent | > 40 | > 40 | Split — polarizing sector |

## Breadth Velocity

Velocity delta over 15m, 30m, 1h windows.

```
velocity_15m = breadth_now - breadth_15m_ago
```

| Velocity | Meaning | Action |
|----------|---------|--------|
| > +15 | Rapidly broadening | Aggressive attention boost for sector |
| +5 to +15 | Gradually improving | Moderate attention boost |
| -5 to +5 | Flat | No breadth bias |
| -15 to -5 | Gradually narrowing | Reduce attention weight |
| < -15 | Rapidly narrowing | Caution — avoid new entries |

**Scalping-specific:** 15m velocity > +20 in CONTRACTION regime = potential regime flip. Attention Engine should increase scan frequency.

## Sector Classification

Metadata Layer menyediakan sektor per symbol (dari Symbol Registry / user config).

### Primary Sectors

| Sector | Description |
|--------|-------------|
| AI | Artificial intelligence, compute, agents |
| MEME | Meme coins, community tokens |
| DEFI | Decentralized finance |
| L1 | Layer 1 blockchains |
| L2 | Layer 2 scaling |
| INFRA | Infrastructure, middleware |
| RWA | Real-world assets |
| GAMING | Gaming, metaverse |
| DEPIN | Decentralized physical infrastructure |
| ORACLE | Oracle networks |
| DEX | Decentralized exchange tokens |
| UNKNOWN | Unclassified (fallback) |

### Classification Rules

1. **API source:** Symbol Registry provides sector assignment (from CoinGecko / manual)
2. **Fallback:** If sector unknown → `UNKNOWN`
3. **Multi-sector:** Symbol can have primary + secondary sector. Breadth computed for primary only. Secondary used for multi-sector analysis.
4. **Reclassification:** Sector change triggers re-computation of sector breadth for both old and new sector

## Leader Breadth

Basket of large-cap leaders. Breadth used as context for Attention Engine.

### Leader Basket

```yaml
leaders:
  - BTC
  - ETH
  - SOL
```

### Leader Metrics

```json
{
  "leaders": {
    "BTC": { "rs_percentile": 75, "breadth_contribution": "positive" },
    "ETH": { "rs_percentile": 62, "breadth_contribution": "neutral" },
    "SOL": { "rs_percentile": 88, "breadth_contribution": "positive" }
  },
  "leader_breadth": 66,
  "leader_velocity_15m": 5
}
```

| Metric | Description |
|--------|-------------|
| `leader_breadth` | % of leaders with RS > 50 |
| `leader_velocity` | Breadth velocity of leader basket |
| `breadth_contribution` | Does this leader pull breadth up or down? |

**Usage:** Jika leader_breadth > 70 dan sector_breadth > 70, Attention Engine memberi confidence boost pada sektor tersebut.

## Breadth Quality

Pattern classification for high-level market context.

| Quality | Criteria | Meaning |
|---------|----------|---------|
| **BROAD** | ≥ 3 sectors with breadth > 60 | Healthy market, multiple narratives |
| **NARROW** | ≤ 2 sectors with breadth > 60 | Leadership concentrated, fragile |
| **DIVERGENT** | ≥ 2 sectors with opposite regime (e.g. AI=80, MEME=20) | Rotation in progress |

## Breadth Store

Read-only store for consumers.

```python
# Get latest breadth snapshot
get_breadth() -> BreadthSnapshot

# Get sector breadth
get_sector_breadth(sector) -> SectorBreadth

# Get leader breadth
get_leader_breadth() -> LeaderBreadth

# Get breadth history (for velocity)
get_breadth_history(minutes=60) -> List[BreadthSnapshot]

# Get regime
get_breadth_regime() -> str
```

## Consumer Map

| Consumer | Reads | What |
|----------|-------|------|
| Stage 5: Attention Engine | Sector breadths, regime, leader breadth | Bias per sector + global risk context |
| Stage 6: Tier Assignment | Breadth regime | Adjust tier thresholds (expansion = tighter? contraction = looser?) |
| Stage 8: Edge Engine | Regime, sector breadth, velocity | Filter edges by regime compatibility |
| Special Situation | Not applicable | Breadth not used for special situations |

## Update Frequency

| Metric | Frequency | Rationale |
|--------|-----------|-----------|
| Global breadth | Every Normalization cycle (~15s) | Changes with each RS update |
| Sector breadth | Every Normalization cycle | Same cadence |
| Velocity | Every 15m window | Meaningful delta needs time |
| Regime | Every cycle but transition requires 2 consecutive readings | Prevents regime flip-flop |

## Non-Goals (V1)

- Breadth prediction (forecasting future breadth)
- Cross-exchange breadth aggregation
- Breadth-based position sizing
- Sector rotation engine (breadth is input, not decision)

## Consequences

**Positive:**
- Breadth gives Attention Engine market context — prevents false positives on isolated moves
- Bull/Bear dual axis captures short opportunities, not just longs
- Velocity enables regime change detection faster than price alone
- Leader breadth anchors sector analysis to large-cap health
- Broad/Narrow/Divergent quality helps Edge Engine choose strategy

**Negative:**
- Breadth depends on sector classification — wrong classification = misleading breadth
- Regime transitions need 2 consecutive readings — adds lag, but prevents whipsaw
- Velocity over 15m requires 15m of runtime before meaningful
- Leader basket is hardcoded — if BTC/ETH/SOL lose dominance, basket must update

## References

- ADR-003: Screener Architecture (Stage 4: Market Breadth)
- ADR-005: Feature Normalization
- ADR-007: Attention Allocation
- SPEC-Sector-Classification.md
