# SPEC-Symbol-State

**Status:** DRAFT  
**Date:** 2026-07-27  
**Owner:** Lead Architect  

---

## Purpose

Definisi single source of truth untuk state setiap symbol. Semua komponen — Feature Store, Normalization, Breadth, Attention, Tier, Edge — membaca dan menulis ke object yang sama. Tidak ada duplikasi state.

## SymbolState Object

```python
@dataclass
class SymbolState:
    # Identity
    symbol: str                    # TAOUSDT
    exchange: str                  # BYBIT | BINANCE
    status: SymbolStatus           # ACTIVE | WARMUP | STALE | DELISTED

    # Metadata (from Symbol Registry)
    metadata: SymbolMetadata

    # Market data (latest tick)
    market: MarketSnapshot

    # Raw features (from Feature Store)
    features: dict[str, FeatureValue]     # feature_id → FeatureValue

    # Normalized features (from Normalization Layer)
    normalized: dict[str, NormalizedValue] # feature_id → NormalizedValue

    # Breadth context (from Market Breadth)
    breadth: BreadthContext | None

    # Attention scores (from Attention Engine)
    attention: AttentionRecord | None

    # Tier assignment (from Tier Assignment)
    tier: TierInfo | None

    # Edge results (from Edge Engine)
    edge_results: dict[str, EdgeResult]   # edge_id → EdgeResult

    # Timestamps
    created_at: datetime
    updated_at: datetime
    last_feature_update: datetime | None
    last_edge_evaluation: datetime | None
```

## Sub-Objects

### SymbolStatus

```python
SymbolStatus = Literal["ACTIVE", "WARMUP", "STALE", "DELISTED"]
```

| Status | Meaning |
|--------|---------|
| ACTIVE | Full pipeline participation |
| WARMUP | New listing, first 24h — limited eval |
| STALE | No data received for > 5 min |
| DELISTED | Removed from universe |

### SymbolMetadata

```python
@dataclass
class SymbolMetadata:
    sector: str                    # AI, MEME, DEFI, ...
    sector_secondary: str | None
    listing_age_days: int
    market_cap_tier: str           # large | mid | small
    tags: list[str]                # ["decentralized-ai", "compute"]
    listed_at: datetime
```

### MarketSnapshot

```python
@dataclass
class MarketSnapshot:
    price: float
    volume_24h: float
    oi: float
    funding_rate: float
    mark_price: float
    index_price: float
    bid: float
    ask: float
    spread: float
    updated_at: datetime
```

### FeatureValue

```python
@dataclass
class FeatureValue:
    feature_id: str
    feature_version: int
    raw_value: float | int | bool | str | None
    raw_unit: str
    updated_at: datetime
    age_seconds: float
    source_event: str
    data_freshness: Literal["FRESH", "STALE", "EXPIRED", "MISSING"]
```

### NormalizedValue

```python
@dataclass
class NormalizedValue:
    feature_id: str
    percentile_7d: float | None
    percentile_30d: float | None
    percentile_90d: float | None
    zscore_30d: float | None
    rank_30d: int | None
    normalized_score: float | None
    window_size: str
    scope: str                       # universe | sector | exchange
    normalized_at: datetime | None
```

### BreadthContext

```python
@dataclass
class BreadthContext:
    sector: str
    sector_bull_breadth: float
    sector_bear_breadth: float
    sector_velocity_15m: float
    sector_velocity_30m: float
    sector_volume_breadth: float
    global_breadth: float
    breadth_regime: str              # CONTRACTION | NEUTRAL | EXPANSION | EUPHORIA
    breadth_quality: str             # BROAD | NARROW | DIVERGENT
    leader_breadth: float
    leader_velocity: float
```

### AttentionRecord

```python
@dataclass
class AttentionRecord:
    attention_score: float           # 0-100
    heat_score: float                # 0-100
    attention_velocity_15m: float
    attention_components: dict[str, float]
    reason_codes: list[str]
    top_reasons: list[str]
    decay_factor: float
    sticky_duration_remaining: int
    promotion_candidate: bool
    demotion_candidate: bool
    calculated_at: datetime
```

### TierInfo

```python
@dataclass
class TierInfo:
    tier: Literal["A", "B", "C", "D"]
    capacity: int | None
    sticky_remaining_cycles: int
    promotion_count: int
    tier_residency_cycles: int
    assigned_at: datetime
```

### EdgeResult

```python
@dataclass
class EdgeResult:
    edge_id: str
    edge_version: int
    direction: Literal["LONG", "SHORT", "NEUTRAL"]
    edge_score: float                # 0-100
    confidence: float                # 0.0-1.0
    reason_codes: list[str]
    feature_values_used: dict
    execution_time_ms: float
    evaluated_at: datetime
```

## JSON Serialization (Wire Format)

```json
{
  "symbol": "TAOUSDT",
  "exchange": "BINANCE",
  "status": "ACTIVE",
  "metadata": {
    "sector": "AI",
    "listing_age_days": 820,
    "market_cap_tier": "large"
  },
  "market": {
    "price": 425.10,
    "volume_24h": 120000000,
    "oi": 8500000000,
    "funding_rate": 0.0001,
    "spread": 0.02
  },
  "features": {
    "F002": { "feature_id": "F002", "raw_value": 3.42, "data_freshness": "FRESH" }
  },
  "normalized": {
    "F002": { "percentile_30d": 94, "normalized_score": 94 }
  },
  "breadth": {
    "sector_bull_breadth": 82,
    "breadth_regime": "EXPANSION"
  },
  "attention": {
    "attention_score": 86,
    "heat_score": 92
  },
  "tier": {
    "tier": "A",
    "sticky_remaining_cycles": 25
  },
  "edge_results": {
    "E001": { "edge_id": "E001", "direction": "LONG", "edge_score": 88 }
  }
}
```

## Access Patterns

| Consumer | Reads | Writes |
|----------|-------|--------|
| Feature Store | — | `features`, `market` |
| Normalization | `features` | `normalized` |
| Market Breadth | `normalized` | `breadth` |
| Attention Engine | `normalized`, `breadth`, `metadata` | `attention` |
| Tier Assignment | `attention` | `tier` |
| Edge Engine | `features`, `normalized`, `breadth`, `attention`, `tier` | `edge_results` |
| Signal Aggregator | `edge_results` | — |

## State Ownership

| Field | Owner | Mutability |
|-------|-------|------------|
| `metadata` | Symbol Registry | Read-only after init |
| `market` | Feature Store | Overwritten on each tick |
| `features` | Feature Store | Overwritten on each feature compute |
| `normalized` | Normalization Layer | Overwritten on each normalization cycle |
| `breadth` | Market Breadth | Overwritten on each breadth cycle |
| `attention` | Attention Engine | Overwritten on each attention cycle |
| `tier` | Tier Assignment | Overwritten on each tier assignment |
| `edge_results` | Edge Engine | Overwritten on each edge evaluation |

No field modified by two different owners.

## Concurrency

- SymbolState per symbol is independent — no cross-symbol locking
- Each owner writes their own field only
- Readers may see stale field if owner hasn't updated this cycle — checked via `updated_at`

## References

- ADR-003: Screener Architecture
- ADR-004: Feature Store
- ADR-007: Attention Allocation
- ADR-010: Edge Framework
