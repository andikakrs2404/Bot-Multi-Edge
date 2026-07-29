# SPEC-Sector-Classification

**Status:** DRAFT  
**Date:** 2026-07-27  
**Owner:** Lead Architect  

---

## Purpose

Menentukan primary sector untuk setiap symbol. Setiap symbol hanya boleh memiliki **1 primary sector**. Multi-sector assignment dilarang karena Breadth Engine harus deterministik — jika TAU masuk AI dan DePIN sekaligus, AI Breadth dan DePIN Breadth terdistorsi.

Sector Classification adalah dependency langsung untuk:

- ADR-006 Market Breadth (sector breadth per sector)
- ADR-007 Attention (sector_breadth bonus)
- SS005 Leader Follower (follower detection per sector)
- SS006 Sector Rotation (rotation detection)
- Future Relative Strength Engine (RS per sector)

## Sector Registry (V1)

| ID | Sector | Description | Examples |
|----|--------|-------------|----------|
| SEC001 | AI | Artificial intelligence, compute, agents | TAO, FET, RNDR, AKT, IO |
| SEC002 | MEME | Meme coins, community tokens, culture coins | DOGE, PEPE, WIF, BONK |
| SEC003 | L1 | Layer 1 blockchains | BTC, ETH, SOL, AVAX, NEAR |
| SEC004 | L2 | Layer 2 scaling solutions | ARB, OP, MATIC, METIS |
| SEC005 | DEFI | Decentralized finance | AAVE, UNI, CRV, MKR, SNX |
| SEC006 | RWA | Real-world assets | ONDO, MPL, CFG, POLYX |
| SEC007 | DEPIN | Decentralized physical infrastructure | HNT, AKT, FIL, AR, IOTX |
| SEC008 | GAMING | Gaming, metaverse, gamefi | GALA, SAND, AXS, IMX, BEAM |
| SEC009 | INFRA | Infrastructure, middleware, interoperability | LINK, DOT, ATOM, WORMHOLE |
| SEC010 | PRIVACY | Privacy coins, zero-knowledge | XMR, ZEC, SCRT, RAIL |
| SEC011 | EXCHANGE | Exchange tokens | BNB, OKB, CRO, KCS |
| SEC999 | UNKNOWN | Fallback — unspecified | Anything not classified |

## Classification Contract

```python
@dataclass
class SectorClassification:
    symbol: str
    exchange: str
    primary_sector: str        # SEC001, SEC002, ..., SEC999
    confidence: float          # 0.0-1.0 (how sure is this classification)
    source: str                # manual | coingecko | coinmarketcap | token_tags | unknown
    updated_at: datetime
```

### Constraints

- **One primary sector per symbol.** No multi-sector.
- **UNKNOWN fallback.** If no source provides classification, assign SEC999.
- **Immutable after init** in a single run. Sector only changes on explicit reclassification.

## Source Priority

Klasifikasi crypto berubah cepat (narrative shifts). Source priority menentukan hierarki kepercayaan.

| Priority | Source | Description | Update frequency |
|----------|--------|-------------|-----------------|
| 1 | **Manual** | Hardcoded override in config/registry | On change |
| 2 | **CoinGecko** | Categories API | Daily sync |
| 3 | **CoinMarketCap** | Categories API | Daily sync |
| 4 | **Exchange Tags** | Bybit/Binance symbol info tags | On symbol_added |
| 5 | **UNKNOWN** | Fallback — SEC999 | Immediate |

### Resolution Logic

```python
def classify(symbol: str) -> SectorClassification:
    if symbol in manual_registry:
        return manual_registry[symbol]  # priority 1
    if symbol in coingecko_categories:
        return coingecko_mapping[symbol]  # priority 2
    if symbol in coinmarketcap_categories:
        return cmc_mapping[symbol]  # priority 3
    if symbol in exchange_tags:
        return exchange_tags_mapping[symbol]  # priority 4
    return UNKNOWN  # priority 5
```

### Reclassification

```yaml
reclassification:
  trigger: Manual edit, source update, or scheduled review
  cooldown: 24h (prevent flip-flop if sources disagree)
  notification: Emit symbol_metadata event on change
```

Sector change triggers re-computation of sector breadth for both old and new sectors (ADR-006).

## Sector Leaders

Basket of sector leaders per sector. Used by SS005 (Leader Follower), ADR-006 (Leader Breadth).

```yaml
sector_leaders:
  AI: [TAO, FET, RNDR]
  MEME: [DOGE, PEPE, WIF]
  L1: [BTC, ETH, SOL]
  L2: [ARB, OP]
  DEFI: [AAVE, UNI, CRV]
  RWA: [ONDO]
  DEPIN: [HNT, AKT]
  GAMING: [GALA, SAND, AXS]
  INFRA: [LINK, DOT]
  PRIVACY: [XMR]
  EXCHANGE: [BNB]
  UNKNOWN: []
```

### Leader Selection Criteria

1. Market cap top 3 in sector
2. Volume liquidity > $10M daily
3. At least 90d listing age
4. Manual override possible

## Breadth Integration

Sector Classification output yang wajib tersedia untuk Market Breadth (ADR-006):

```yaml
sector_size:       # symbol count per sector
sector_rank:       # sector ranking by market cap
sector_breadth:    # computed by Market Breadth, input per sector
sector_leaders:    # leader basket per sector
```

## Classification Lifecycle

```
UNCLASSIFIED
    │
    ▼
CLASSIFIED
    │
    ├── Review pending? ──► REVIEW_PENDING ──► CLASSIFIED (re-assign)
    │
    └── No issues ──► CLASSIFIED (steady state)
```

| Status | Meaning |
|--------|---------|
| UNCLASSIFIED | No source found. SEC999 assigned |
| CLASSIFIED | Valid sector assigned |
| REVIEW_PENDING | Sector flagged for review (source disagreement, narrative shift) |

### Auto-Review

```yaml
review_cycle_days: 90
trigger: >
  Symbol in UNKNOWN > 90 days → flag for manual review.
  Source conflict (CoinGecko says AI, CMC says DEPIN) → REVIEW_PENDING.
```

## Classification Output

Per symbol, tersedia melalui Metadata Layer:

```json
{
  "symbol": "TAOUSDT",
  "exchange": "BINANCE",
  "primary_sector": "AI",
  "confidence": 0.95,
  "source": "coingecko",
  "updated_at": "2026-07-27T00:00:00.000Z",
  "leaders_in_sector": ["TAO", "FET", "RNDR"],
  "sector_size": 45
}
```

## Registry File (sectors.yaml)

```yaml
# sectors.yaml — hot-reloadable
sectors:
  AI:
    id: SEC001
    leaders: [TAO, FET, RNDR]
    description: "AI tokens"

  MEME:
    id: SEC002
    leaders: [DOGE, PEPE, WIF]
    description: "Meme coins"

  # ... all 11 sectors

manual_overrides:
  # Symbol → sector overrides (priority 1)
  RENDERUSDT: AI
  NEARUSDT: L1
```

## Metrics

| Metric | Description |
|--------|-------------|
| `classified_symbols` | Count of symbols with sector ≠ UNKNOWN |
| `unknown_symbols` | Count of SEC999 |
| `classification_changes_24h` | Reclassifications in last 24h |
| `review_pending_count` | Symbols flagged for review |
| `sector_sizes` | Distribution per sector |

## Non-Goals (V1)

- Multi-sector tags (symbol CAN have secondary sector for future analysis, but NOT used for breadth)
- Dynamic sector creation (new sectors require config update)
- ML-based sector classification
- Narrative change detection

## References

- ADR-006: Market Breadth
- ADR-007: Attention Allocation
- SPEC-Special-Situations (SS005 Leader Follower)
