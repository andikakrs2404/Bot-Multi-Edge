# ADR-004: Feature Store

**Status:** DRAFT  
**Date:** 2026-07-28  
**Author:** Lead Architect  
**Deciders:** Lead Architect  

---

## Context

Feature Store adalah jantung pipeline. Setelah Market Data Layer me-normalisasi raw exchange feed, setiap event harus:

1. **Feature computed once** — tidak ada dua edge yang recompute metric sama
2. **Feature normalised before use** — BFS normalization, percentile/rank registry-wide
3. **Feature versioned** — setiap update punya version counter untuk replay detection
4. **Feature freshness tracked** — stale feature (>TTL) dianggap unavailable

Tanpa Feature Store, edge engine harus recompute feature dari raw data setiap kali — waste CPU, inkonsisten hasil antar edge.

## Decision

Build **enriched event store** dengan single-pass feature computation dan sliding window state per symbol.

```
Event Bus (normalised)
    │
    ▼
Feature Store (single-pass)
    │
    ├── Raw Features        →  1000+ symbol × ~12 features  (ring buffer)
    ├── Feature Version     →  monotonically increasing per symbol-feature
    ├── Feature Freshness   →  last_updated + expiry TTL per type
    └── Feature Event       →  published back to bus for Normalization step
```

## Architecture

```
MarketDataEvent
    │
    ▼
FeatureStore.ingest(event)
    │
    ├── ticker     → update price, volume, oi, funding, bid/ask spread
    ├── trade      → update vwap, trade count, volume profile
    ├── candle_1m  → compute OHLCV delta, momentum, volatility
    ├── candle_15m → compute swing metrics
    ├── candle_1h  → compute macro metrics
    ├── open_interest → OI direction, OI change %
    ├── funding    → funding rate z-score
    └── liquidation → liquidation imbalance
    │
    ▼
FeatureUpdateEvent (published to bus)
    │
    ▼
Normalization (ADR-005)
```

### Feature Registry

Setiap feature didefinisikan dalam registry:

| Feature | Source Event | Window | TTL | Description |
|---------|-------------|--------|-----|-------------|
| `price` | ticker | latest | 5s | Last traded price |
| `volume_1m` | ticker | 1m sliding | 60s | Volume in last minute |
| `vwap_1m` | trade | 1m sliding | 60s | Volume-weighted avg price |
| `oi` | open_interest | latest | 60s | Open interest |
| `oi_change_1m` | open_interest | 1m | 65s | OI change % 1m |
| `funding_rate` | funding | latest | 480s | Funding rate |
| `funding_zscore` | funding | 8h rolling | 600s | Z-score vs 8h window |
| `trade_count_1m` | trade | 1m sliding | 60s | Number of trades |
| `bid_ask_spread` | ticker | latest | 5s | (ask-bid)/mid |
| `volume_delta` | ticker | 1m | 60s | Buy vol - sell vol |
| `high_1m` | candle_1m | 1m | 60s | 1m high |
| `low_1m` | candle_1m | 1m | 60s | 1m low |
| `volatility_1m` | candle_1m | 1m | 60s | (high-low)/close |
| `oi_1h_change` | open_interest | 1h | 3600s | OI change % 1h |
| `liquidation_imbalance` | liquidation | 1m | 60s | (long liq - short liq)/total |
| `rsi_14_1m` | candle_1m | 14 periods | 120s | RSI from 1m candles |

### Feature Data Model

```python
@dataclass(slots=True, kw_only=True)
class RawFeature:
    feature: str          # feature name from registry
    value: float
    symbol: str
    exchange: str
    version: int
    computed_at: float    # monotonic timestamp
    freshness: int        # TTL in seconds

@dataclass(slots=True, kw_only=True)
class FeatureUpdateEvent(Event):
    exchange: str
    symbol: str
    features: dict[str, RawFeature]   # all features updated this tick
```

### FeatureStore State (in-memory)

```python
# Per symbol, per feature — single source of truth
{
  "BTCUSDT": {
    "price":        RawFeature(value=65000.0, version=1423, computed_at=..., freshness=5),
    "volume_1m":    RawFeature(value=1250.0,  version=1423, computed_at=..., freshness=60),
    "oi":           RawFeature(value=1.2e9,   version=1423, computed_at=..., freshness=60),
    ...
  },
  "ETHUSDT": { ... }
}
```

## Feature Ownership

| Producer | Features |
|----------|----------|
| Ticker handler | price, volume_1m, oi, funding_rate, bid_ask_spread |
| Trade handler | vwap_1m, trade_count_1m, volume_delta |
| Candle handler | high_1m, low_1m, volatility_1m, rsi_14_1m |
| OpenInterest handler | oi_change_1m, oi_1h_change |
| Funding handler | funding_zscore |
| Liquidation handler | liquidation_imbalance |

## Data Flow Detail

```
1. MarketDataEvent arrives at FeatureStore.ingest()
2. router_classifier → TickerHandler / TradeHandler / CandleHandler / etc.
3. handler computes 1+ features, returns list[RawFeature]
4. FeatureStore version bump per symbol-feature
5. FeatureUpdateEvent built and published to bus
6. Downstream: Normalization (ADR-005) subscribes to FeatureUpdateEvent
```

```
[1] ingest(MarketDataEvent)
      │
      ▼
[2] route_by_event_type()
      │
      ├── EventType.TICKER        → TickerHandler
      ├── EventType.TRADE         → TradeHandler
      ├── EventType.CANDLE_1M     → CandleHandler
      ├── EventType.OPEN_INTEREST → OpenInterestHandler
      ├── EventType.FUNDING       → FundingHandler
      └── EventType.LIQUIDATION   → LiquidationHandler
      │
      ▼
[3] handler.update(symbol, raw_event) → list[RawFeature]
      │
      ▼
[4] FeatureStore._apply(symbol, RawFeature[])
      │  bump version
      │  store in _features[exchange][symbol][feature]
      │  update freshness
      │
      ▼
[5] publish FeatureUpdateEvent to EventBus
```

## Feature Freshness & TTL

- Setiap feature punya `freshness` (TTL detik)
- Jika `now() - computed_at > freshness` → feature stale
- Stale feature tidak dikirim ke Normalization
- FeatureStore.get(symbol, feature) return None jika stale
- Cross-check: `FeatureStore.check_freshness()` periodic task tiap 30s

## Feature Versioning

- Setiap symbol-feature pair punya version counter
- Version increment setiap kali feature diperbarui
- Normalization layer bisa detect version jump → recalculate percentile
- Version skip (gap >1) → potential missed update → warn di log

## Non-Goals (V1)

- Persistence — semua in-memory, replay dari event store nanti
- Feature derivation engine — feature manual didefinisikan, bukan auto-generated
- Cross-symbol features — breadth, correlation, etc. di ADR-006
- Feature importance tracking — Weight & Biases integration ditunda

## Consequences

**Positive:**
- Single-pass computation — setiap event diproses sekali, semua edge dapet feature
- TTL mencegah stale feature dipakai edge — pipeline fail-safe
- Versioning memudahkan replay detection dan debug
- Ring buffer memory-bound — tidak leaking

**Negative:**
- Feature Store jadi single point of latency — handler bottleneck
- Memory grows O(symbols × features) — 1000×16 = 16K entries, OK
- TTL tuning per-feature perlu benchmark real-time

## References

- ADR-002: Market Data Layer (event types consumed)
- ADR-005: Normalization (consumer of FeatureUpdateEvent)
- ADR-003: Screener Architecture (pipeline placement)
- VectorBT: OSS reference for factor computation
- NautilusTrader: reference for feature registry pattern

## Design Answers

| Question | Decision |
|----------|----------|
| Where do features live? | In-memory dict per symbol, per exchange |
| How is freshness tracked? | TTL per feature definition |
| How to add new feature? | Add handler + registry entry |
| Feature store persistence? | No persistence in V1 (in-memory only) |
| Event lost during feature computation? | Resend from WS replay — not ACK-based |
| Feature registry config file? | Yes — TOML/YAML in V2, hardcoded in V1 |
| How to detect feature source issues? | FeatureStore health endpoint + coverage metric |
