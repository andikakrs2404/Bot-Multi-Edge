# ADR-005: Feature Normalization

**Status:** DRAFT  
**Date:** 2026-07-27  
**Author:** Lead Architect  
**Deciders:** Lead Architect  

---

## Context

Feature Store (ADR-004) menyimpan **raw values**. Dua symbol dengan raw value sama belum tentu equally interesting — konteks distribusi universe penting.

```
BTCUSDT  OI Expansion = 2.5%   → mungkin P95 di BTC
DOGEUSDT OI Expansion = 6.0%   → mungkin P60 di DOGE
```

Without normalization, Attention Engine dan Edge Engine tidak bisa bandingkan feature antar symbol secara adil.

## Decision

Build **Feature Normalization Layer** sebagai stage eksplisit antara Feature Store dan semua consumer. Output-nya adalah Normalization Store terpisah — tidak menulis kembali ke Feature Store.

```
Feature Store (raw)
    │
    ▼
Normalization Layer
    │
    ▼
Normalization Store
    │
    ├──► Market Breadth (Stage 4)
    ├──► Attention Engine (Stage 5)
    └──► Edge Engine (Stage 8)
```

## Architecture

```
Raw Feature (from Feature Store API)
    │
    ▼
Freshness Gate
    │
    ├── FRESH ──► Normalizer
    │
    └── STALE/EXPIRED ──► Skip (preserve last normalized value)
              │
              ▼
        Normalization Store
        (per symbol, per feature, per window)
              │
              ▼
        NormalizedFeatureState
        { symbol → { feature_id → { percentile, zscore, rank, normalized_score } } }
```

### Components

| Component | Role |
|-----------|------|
| **Freshness Gate** | Check `age_seconds` vs `freshness_ttl_sec` per feature. Skip STALE/EXPIRED. |
| **Normalizer** | Compute percentile (primary), z-score, rank, normalized_score per feature per window |
| **Normalization Store** | Read-only store of normalized values. Consumers read from here, not Feature Store for normalized data. |

## Input

From Feature Store API:

```json
{
  "symbol": "BTCUSDT",
  "exchange": "BYBIT",
  "feature_id": "F002",
  "feature_version": 1,
  "raw_value": 2.5,
  "updated_at": "2026-07-27T12:00:00.052Z",
  "age_seconds": 0.15,
  "data_freshness": "FRESH"
}
```

## Output

```json
{
  "symbol": "BTCUSDT",
  "exchange": "BYBIT",
  "feature_id": "F002",
  "feature_version": 1,
  "raw_value": 2.5,
  "percentile_7d": 92,
  "percentile_30d": 95,
  "percentile_90d": 88,
  "zscore_30d": 2.1,
  "rank_30d": 42,
  "normalized_score": 92,
  "normalized_at": "2026-07-27T12:00:00.100Z",
  "window_size": "30d",
  "scope": "universe"
}
```

### Field Definitions

| Field | Description |
|-------|-------------|
| `percentile_7d/30d/90d` | Percentile rank within scope (0-100) |
| `zscore_30d` | Standard deviations from mean |
| `rank_30d` | Absolute rank within universe (1 = highest) |
| `normalized_score` | Weighted composite — used as primary input for attention |
| `window_size` | Which window this output represents |
| `scope` | Normalization universe: universe / sector / exchange |

## Normalization Methods

### Percentile (Primary)

Default method for all features. Rank raw value against population, output 0-100.

```
percentile = (rank_in_universe / population_size) × 100
```

| Feature | Default percentiles |
|---------|-------------------|
| F001 Liquidity | Universe percentile |
| F002 OI Expansion | Universe percentile |
| F003 Volume Expansion | Universe percentile |
| F004 RS | **Sector** percentile (more meaningful than universe) |
| F005 Compression | Universe percentile |
| F006 Funding Rate | Universe percentile (long tail) |

### Z-Score (Anomaly Detection)

Optional — used for features where outlier detection matters.

```
zscore = (value - μ) / σ
```

| Feature | When used |
|---------|-----------|
| F006 Funding Rate | Detect extreme funding > 3σ |
| Spread (future) | Detect liquidity crisis |
| Liquidation (future) | Detect cascade |

### Rank

Absolute ordering within universe. Used where relative position is more informative than distance.

```
rank = position in sorted list (1 = highest)
```

| Feature | When used |
|---------|-----------|
| F004 RS | RS rank for sector comparison |
| F001 Liquidity | Liquidity rank for tier decisions |

## Normalization Scope

Scope menentukan population untuk perhitungan percentile/rank.

| Scope | Description | Used for |
|-------|-------------|----------|
| **Universe** | All 250 symbols (from Stage 1) | F001, F002, F003, F005, F006 |
| **Sector** | Symbols within same sector only | F004 RS (compared within sector) |
| **Exchange** | Symbols on same exchange bin | Features needing exchange-level context |

**Rule:** Default scope = universe. Overridden per feature in FEATURE-Registry contract (`normalization_scope` field).

## Window Definition

Tiga jendela waktu paralel. Consumer memilih mana yang relevan.

```yaml
normalization_windows:
  - 7d    # short-term — regime changes, new listings
  - 30d   # medium-term — default for attention
  - 90d   # long-term — baseline, macro regime
```

Setiap feature memiliki `normalized_value` untuk tiap window. Consumer bebas pilih.

| Consumer | Default window |
|----------|---------------|
| Market Breadth | 30d |
| Attention Engine | 30d (fallback: 7d for volatile symbols) |
| Edge Engine | Configurable per edge |
| Tier Promotion/Demotion | 7d (fast reaction) |

## Freshness Gate

Normalizer tidak boleh memproses feature stale atau expired.

```python
if feature.data_freshness in ("STALE", "EXPIRED"):
    skip_normalization()
    preserve_last_normalized_value()
```

| Freshness | Action |
|-----------|--------|
| FRESH | Compute normalization |
| STALE | Use last normalized value, decrease confidence weight |
| EXPIRED | Flag as null — consumer must handle |
| MISSING | Not present — consumer skips |

## Normalization Store

Store terpisah dari Feature Store. Tidak ada mutual write.

```
Normalization Store
├── exchange
├── symbol
├── features: Dict[FeatureID, NormalizedFeatureValue]
├── normalized_at: timestamp
└── version: int
```

```python
# API
get_normalized(exchange, symbol, feature_id, window="30d") -> NormalizedFeatureValue
get_normalized_batch(exchange, symbols, feature_ids, window="30d") -> Dict
get_all_normalized(exchange, scope="universe", window="30d") -> Dict[symbol, Dict[FeatureID, NormalizedFeatureValue]]
```

## Composite Normalized Score

Normalization Layer dapat menghasilkan **feature vectors** — kumpulan normalized values per symbol yang siap dipakai Attention Engine.

```json
{
  "symbol": "BTCUSDT",
  "normalized_features": {
    "F002_OI_EXPANSION":   { "percentile_30d": 95, "normalized_score": 95 },
    "F003_VOLUME_EXPANSION": { "percentile_30d": 88, "normalized_score": 88 },
    "F004_RS":             { "percentile_30d": 91, "normalized_score": 91 },
    "F005_COMPRESSION":    { "percentile_30d": 12, "normalized_score": 12 },
    "F006_FUNDING":        { "percentile_30d": 72, "normalized_score": 72 }
  },
  "feature_vector_length": 5,
  "normalized_at": "2026-07-27T12:00:00.100Z"
}
```

Attention Engine kemudian menggunakan feature vector + weights (from FEATURE-Certification confidence scores) untuk menghitung `heat_score`.

**Note:** Composite normalized score is NOT Heat Score. Heat Score is output of Attention Engine (ADR-007). Normalization Layer hanya menyiapkan normalized feature vectors — perkalian weight terjadi di Attention Engine.

## Per-Feature Normalization Configuration

Extended from FEATURE-Registry contract:

```yaml
feature_id: F004
normalization:
  scope: sector
  methods:
    - percentile_30d
    - rank_30d
  windows: [7d, 30d, 90d]
  default_window: 30d
  zscore_enabled: false
```

Default values if not specified:
- `scope: universe`
- `methods: [percentile_30d]`
- `windows: [30d]`
- `default_window: 30d`
- `zscore_enabled: false`

## Consumer Map

| Consumer | Reads from | What |
|----------|-----------|------|
| Stage 4: Market Breadth | Normalization Store | Normalized RS per symbol for sector breadth computation |
| Stage 5: Attention Engine | Normalization Store | Feature vectors + weights → heat_score |
| Stage 8: Edge Engine | Normalization Store | Normalized values per edge strategy |
| Special Situation | Feature Store (raw) | Skips normalization — acts on raw events |

## Non-Goals (V1)

- Feature Store write-back (normalization never writes to Feature Store)
- ML-based normalization (autoencoders, learned percentiles)
- Real-time window recomputation (windows computed on schedule, not per tick)
- Cross-exchange normalization (symbol on Bybit vs Binance normalized separately)

## Consequences

**Positive:**
- Raw vs normalized separation keeps both layers simple and testable
- Multiple windows (7d/30d/90d) give consumers flexibility without Feature Store bloat
- Freshness gate prevents stale data from contaminating attention/edge
- Composite normalized feature vectors give Attention Engine clean input
- Per-feature scope config (universe/sector/exchange) enables context-aware comparison

**Negative:**
- Extra hop before Market Breadth / Attention — adds ~2s latency per cycle
- Normalization Store doubles in-memory state (raw + normalized)
- Window management: maintaining rolling 7d/30d/90d windows across 250 symbols × 6 features requires ~4500 sliding buffers
- Sector normalization depends on Metadata Layer (sector assignment) — if metadata wrong, normalization wrong

## References

- ADR-003: Screener Architecture (Stage 3: Normalization)
- ADR-004: Feature Store
- FEATURE-Registry.md
- FEATURE-Certification.md
