# ADR-002: Market Data Layer

**Status:** DRAFT  
**Date:** 2026-07-27  
**Author:** Lead Architect  
**Deciders:** Lead Architect  

---

## Context

Pipeline dimulai dari koneksi ke exchange. Bybit Futures dan Binance Futures punya WS protocol, rate limit, dan data schema berbeda. Screener perlu data real-time yang seragam tanpa peduli asal exchange.

Market Data Layer harus isolasi kompleksitas exchange dari seluruh pipeline di atasnya.

## Decision

Build **exchange adapters** yang normalize semua WS feed ke internal event schema. Satu adapter per exchange. Pipeline hanya lihat normalised events.

## Architecture

```
Exchange

↓
Connection Manager
(reconnect, heartbeat, rate limit)

↓
Raw Event
(exchange-native format, stored for debug)

↓
Normaliser
(map exchange fields → common schema)

↓
Sequence Validator
(detect gaps, duplicates, out-of-order)

↓
Timestamp Enrichment
(exchange_ts, received_ts, normalized_ts)

↓
Event Bus
(priority queue per event type)

↓
Pipeline
```

**Parallel path:**

```
Symbol Registry ──► Metadata Events
(dynamic discovery,
 delisting tracking,
 listing age,
 sector,
 tags)
```

### Adapter Responsibilities

| Component | Job |
|-----------|-----|
| **Connection Manager** | WS connect, auth, heartbeat, reconnect backoff, rate limit tracking |
| **Raw Event Store** | Buffer raw exchange payload before normalisation (debug/troubleshoot) |
| **Normaliser** | Map exchange-specific fields → common schema |
| **Sequence Validator** | Detect missing/duplicate/out-of-order sequences per symbol |
| **Timestamp Enricher** | Attach exchange_ts, received_ts, normalized_ts to every event |
| **Health Monitor** | Track latency, disconnects, sequence gaps |
| **Symbol Registry** | Auto-discover symbols, track delisting/new listing, store metadata |

## Event Schema

Setiap event dari adapter memiliki shape seragam:

```json
{
  "exchange": "BYBIT",
  "symbol": "BTCUSDT",
  "event": "ticker",
  "priority": "medium",
  "data": {
    "price": 120000.50,
    "volume_24h": 1250000.0,
    "oi": 8500000000.0,
    "funding_rate": 0.0001,
    "mark_price": 120010.00,
    "index_price": 119990.00,
    "bid": 119999.00,
    "ask": 120001.00,
    "spread": 2.0
  },
  "timestamps": {
    "exchange_ts": "2026-07-27T12:00:00.000Z",
    "received_ts": "2026-07-27T12:00:00.050Z",
    "normalized_ts": "2026-07-27T12:00:00.052Z"
  }
}
```

### Event Types

| Event | Priority | Trigger | Payload |
|-------|----------|---------|---------|
| `trade` | **high** | Each trade | Price, size, side, timestamp |
| `liquidation` | **high** | Liquidation event | Price, size, side |
| `connection_status` | **high** | WS connect/disconnect | Status, reason, sequence, gap count |
| `ticker` | medium | Price/volume/OI change | Current price, volume, OI, funding, bid/ask |
| `funding` | medium | Funding rate update | Rate, predicted rate, next settlement |
| `open_interest` | medium | OI update | Total OI, change % |
| `candle_1m` | medium | Every minute | OHLCV |
| `candle_15m` | low | Every 15 min | OHLCV |
| `candle_1h` | low | Every hour | OHLCV |
| `book_snapshot` | low | Order book snapshot (throttled) | 10 best bids/asks |
| `symbol_added` | **high** | New contract listed | Symbol, exchange, listing timestamp |
| `symbol_removed` | **high** | Contract delisted | Symbol, exchange, reason |
| `symbol_metadata` | low | Metadata changed | Symbol, sector, tags, listing age, market cap tier |

## Exchange Adapter Matrix

| Capability | Bybit | Binance |
|------------|-------|---------|
| WS Public URL | wss://stream.bybit.com/v5/public/linear | wss://fstream.binance.com/ws |
| Auth | None (public) | None (public) |
| Rate limit | 50 conn/sec | 5 msg/sec per conn |
| Reconnect | Exponential backoff, max 60s | Exponential backoff, max 60s |
| Sub per conn | 10 symbol streams | 1 stream per symbol (multi-sub via combo) |
| Heartbeat | Ping/Pong every 20s | Ping/Pong every 3min |

## Connection Strategy

Given universe size (500–1000 symbols) and exchange limits:

| Exchange | Connections | Strategy |
|----------|-------------|----------|
| Bybit | 1 connection | Subscribe all symbols in one WS (max 10 per sub, loop) |
| Binance | ~5 connections | Combiner stream per connection, split universe |

Each connection runs in its own thread/async task. Failures isolated — one connection drop does not affect others.

## Event Bus

Publish-subscribe bus between Market Data Layer and downstream consumers (Feature Store, Special Situation Engine).

```
Adapter ──► Event Bus ──► Feature Store
                     ──► Special Situation Engine
                     ──► Metadata Layer
                     ──► Health Dashboard
```

**Properties:**
- Async, non-blocking publish
- Ordered per symbol (same symbol events processed in sequence)
- Subscriber can filter by exchange, symbol, or event type
- Buffer on publish failure (disk-backed for replay)

### Event Priority

Event Bus implements **priority queue** — high priority events (trade, liquidation, connection_status, symbol_added/removed) delivered before medium/low. Prevents liquidation events from being queued behind 1h candle processing.

| Level | Handling |
|-------|----------|
| **high** | Immediate delivery, no queuing delay |
| medium | Ordered per symbol, processed after high |
| low | Batch-processed, may be dropped under backpressure |

## Sequence Integrity

Adapters must detect sequence anomalies to maintain data quality:

| Anomaly | Detection | Action |
|---------|-----------|--------|
| **Missing sequence** | Gap in exchange sequence numbers | Log warning, emit `connection_status` with `gap_detected: true`, increment gap counter |
| **Duplicate sequence** | Same sequence number received twice | Drop duplicate, log warning |
| **Out-of-order** | Sequence number < last processed | Reorder buffer (max 5 slots), if exceeded drop and emit warning |

On reconnect, adapter requests sequence reset and emits `connection_status { status: "reconnected", gap_count: N }`.

## Symbol Registry

Component that auto-discovers and tracks symbol lifecycle:

```
Symbol Registry
  ├── Discover active symbols from exchange REST API (every 1h)
  ├── Track listing age (days since first seen)
  ├── Detect delisting (symbol absent from exchange response for 2 consecutive checks)
  ├── Emit symbol_added / symbol_removed events
  └── Store & serve metadata (sector, tags, market cap tier)
```

**Metadata event flow:**

```
Symbol Registry
     │
     ▼
symbol_metadata event ──► Event Bus ──► Metadata Layer (downstream)
```

**Metadata schema:**

```json
{
  "symbol": "TAOUSDT",
  "exchange": "BINANCE",
  "sector": "AI",
  "tags": ["decentralized-ai", "compute"],
  "listing_age_days": 420,
  "market_cap_tier": "large",
  "status": "ACTIVE"
}
```

## Non-Goals (V1)

- Private/authenticated streams (account orders, positions)
- Order book depth beyond snapshot
- Historical data fetching (separate replay pipeline)
- Multi-connection load balancing

## Consequences

**Positive:**
- Pipeline never touches exchange protocol — pure internal events
- Adding exchange = write one adapter, rest untouched
- Raw event store enables debugging cross-exchange differences
- Event bus enables replay: log all events → replay later
- Priority queue prevents liquidation/trade from being blocked by candle processing
- Sequence integrity catches data corruption early
- Symbol Registry keeps symbol lifecycle explicit (no silent delisting)
- Connection isolation prevents cascade failure

**Negative:**
- Normaliser must handle edge cases (Bybit vs Binance float precision, null fields, symbol naming)
- Event bus ordered-per-symbol constraint adds complexity; naive queue design blocks fast symbols behind slow ones
- WS message rate on 1000 symbols (ticker ~1s each) = ~1000 msg/s; bus must handle this throughput
- Symbol Registry adds external dependency on exchange REST API (1h polling)
- Clock sync between exchange_ts vs received_ts depends on NTP accuracy (~50ms typical)

## Design Answers

| Question | Answer |
|----------|--------|
| **How to handle reconnect?** | Exponential backoff, max 60s. On reconnect → sequence reset, emit `connection_status`. Each connection isolated |
| **How to detect sequence gap?** | Sequence Validator compares seq numbers per symbol. Gap → emit warning + increment counter. Duplicate → drop. Out-of-order → reorder buffer (5 slots) |
| **How timestamps normalised?** | Every event carries `exchange_ts` (from exchange), `received_ts` (local arrival), `normalized_ts` (after normalisation). Enables latency analysis |
| **How new symbol detected?** | Symbol Registry polls exchange REST API every 1h. New symbol → emit `symbol_added` event. Delisted symbol → emit `symbol_removed` |
| **How symbol metadata stored?** | Registry stores sector, tags, listing age, market cap tier. Emits `symbol_metadata` events. Downstream Metadata Layer uses this for feature normalisation and attention bias |

## References

- ADR-001: System Overview
- ADR-003: Screener Architecture
- Bybit WS API Docs
- Binance WS API Docs
