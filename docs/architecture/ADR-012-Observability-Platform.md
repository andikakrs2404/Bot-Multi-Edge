# ADR-012: Observability Platform

**Status:** FROZEN  
**Date:** 2026-07-28  
**Author:** Lead Architect  
**Deciders:** Lead Architect

---

## Context

Pipeline memiliki 11 stage dari Market Data hingga Edge Engine. Setiap stage proses event, compute feature, dan publish hasil ke stage berikutnya. Namun saat ini tidak ada mekanisme untuk:

- Melihat apakah setiap komponen berjalan sesuai ADR
- Mengukur throughput dan latency per stage
- Mendeteksi bottleneck sebelum menyebabkan data loss
- Memverifikasi integrasi antar stage saat development

Tanpa observability, bug pipeline baru ketahuan setelah edge engine output tidak masuk akal — terlambat dan mahal.

## Decision

Build **Observability Platform** terpisah dari trading engine. Bukan dashboard — platform dengan tiga fungsi:

1. **Collect** — metrics dari setiap komponen pipeline via Metrics Bus
2. **Store** — time-series observability data di Observability Store
3. **Serve** — via API untuk dashboard, alerts, dan health monitor

Platform independen dari trading engine runtime. Bisa mati tanpa menghentikan pipeline.

## Architecture

```
Components (Connections, Registry, Feature Store, ...)
    │
    │  publish HealthEvent / MetricsEvent
    ▼
Metrics Bus (EventBus separate from pipeline bus)
    │
    ▼
Observability Store (in-memory ring buffer, TTL)
    │
    ├── Dashboard API (FastAPI, REST + WS)
    ├── Health Monitor (uptime, reconnect count)
    └── Alerts (threshold-based, TBI)
```

## Core Principle: Producer Owns Metrics

Dashboard hanya display. Producer component owning metric definition:

| Metric | Producer | Delivery |
|--------|----------|----------|
| connection_status | ExchangeConnection | EventBus → OBS-002 HealthEvent |
| uptime, reconnect_count | ExchangeConnection | OBS-002 HealthEvent |
| symbol_count, sector_dist | SymbolRegistry | Snapshot API (pull) |
| events_per_sec | EventBus (per-stage) | OBS-001 MetricsEvent via Metrics Bus |
| queue_depth | EventBus | OBS-001 MetricsEvent |
| feature_freshness | FeatureStore | OBS-001 MetricsEvent (V2) |
| attention_distribution | AttentionEngine | OBS-001 MetricsEvent (V3) |
| tier_distribution | TierAssigner | Snapshot API (V3) |
| queue_contents | FocusQueue | WS + snapshot (V3) |
| opportunity_count | OpportunityEngine | OBS-001 MetricsEvent (V4) |
| edge_signal_count | EdgeEngine | OBS-001 MetricsEvent (V5) |

## Snapshot vs Stream

| Data | Snapshot REST | WebSocket Stream | Reason |
|------|-------------|-----------------|--------|
| Connection status | ✅ `GET /api/system/status` | ✅ `/ws/status` | State changes rare, real-time useful |
| Symbol Registry | ✅ `GET /api/symbols` | ❌ | Changes every 5 min, pull enough |
| Symbol detail | ✅ `GET /api/symbols/{symbol}` | ❌ | Per-request lookup |
| Events/sec | ❌ | ✅ `/ws/metrics` | Continuous, no meaningful snapshot |
| Queue depth | ❌ | ✅ `/ws/metrics` | Continuous |
| Feature freshness | ✅ `GET /api/features/freshness` | ✅ `/ws/features` (V2) | Snapshot for overview, WS for drill-down |
| Attention scores | ✅ `GET /api/attention` | ✅ `/ws/attention` (V3) | Both useful |
| Tier distribution | ✅ `GET /api/tiers` | ❌ (V3) | Changes slowly |
| Opportunity queue | ✅ `GET /api/opportunities` | ✅ `/ws/opportunities` (V4) | Real-time needed |
| Edge signals | ✅ `GET /api/edges` | ✅ `/ws/edges` (V5) | Real-time needed |

## V1 Scope

Hanya data dari komponen yang sudah berjalan:

| Source | Data | Format |
|--------|------|--------|
| ExchangeConnection | connection status, uptime, reconnect count | `ConnectionStatus` via OBS-002 |
| SymbolRegistry | total symbols, per-exchange, per-sector | Snapshot API (pull) |

Tidak ada mock. Semua data dari komponen nyata.

## API Contract V1

```
GET  /api/system/status     → connection state, uptime
GET  /api/symbols           → all symbols (paginated)
GET  /api/symbols/{symbol}  → single symbol metadata
WS   /ws/status             → real-time connection status events
```

## Dashboard V1 Pages

### Page 1 — System Overview

```
Exchange Status
  🟢 Bybit    uptime: 2h 14m    reconnects: 0
  🟢 Binance  uptime: 2h 12m    reconnects: 1

Event Bus Health
  Queue Depth: 0
  Subscribers: 3
```

### Page 2 — Symbol Registry

```
Total Symbols: 872

Bybit:       418
Binance:     454

Per Sector:
  LAYER1      95
  DEFI       120
  MEME        90
  AI          48
  ...        ...
  UNKNOWN     12
```

### Page 3 — Symbol Detail

```
BTCUSDT
  Exchange:     BYBIT
  Sector:       LAYER1
  Listing Age:  1,234 days
  Market Cap:   large
  Tags:         ["blue-chip", "perpetual"]
```

## Folder Structure

```
future-trading-bot-rnd/
├── src/                          # trading engine (existing)
├── docs/
├── services/
│   └── observability-api/        # FastAPI backend
│       ├── api.py
│       ├── routers/
│       │   ├── system.py
│       │   └── symbols.py
│       ├── services/
│       │   ├── health.py
│       │   └── registry_view.py
│       └── models.py
└── dashboard/                    # Next.js (V1 minimal)
    ├── app/
    ├── components/
    ├── lib/
    └── hooks/
```

## Data Flow

```
SymbolRegistry._poll()
    │
    ▼
ObservabilityStore.record_symbols(symbols)
    │
    ▼
Dashboard API reads store
    │
    ▼
React renders tables + status

ExchangeConnection.start() / stop() / reconnect
    │
    ▼
EventBus (pipeline) ──┐
                      │
ObservabilityStore.listen(event_bus)
    │
    ▼
WS /ws/status → dashboard real-time
```

ObservabilityStore listen ke pipeline EventBus untuk `ConnectionStatus` event. Tidak perlu publisher terpisah untuk V1.

## Observability Event Contract

Semua observability data dikirim sebagai typed event, bukan dict random:

### OBS-001: MetricsEvent

```python
@dataclass
class MetricsEvent:
    source: str              # "feature_store", "event_bus", "attention"
    name: str                # "events_per_sec", "queue_depth", "event_lag_ms"
    value: float
    tags: dict[str, str]     # {"stage": "normalization", "symbol": "BTCUSDT"}
    timestamp: datetime
```

**Key metric: `event_lag_ms`.** Formula:

```
now - event.timestamps.exchange_ts
```

Dipublish oleh setiap stage setelah receive event. Dashboard:

```
Bybit lag    : 120ms
Binance lag  : 95ms
FeatureStore : 150ms
```

**Key metric: `stage_watermark`.** Timestamp dari event terakhir yang diproses oleh stage:

```python
name="stage_watermark", value=<unix_ms>, tags={"stage": "normalization"}
```

Digunakan dashboard untuk deteksi stage tertinggal.

Dipublish ke Metrics Bus (EventBus terpisah dari pipeline bus). Pipeline bus tidak boleh diblokir oleh observability.

### OBS-002: HealthEvent

```python
@dataclass
class HealthEvent:
    source: str              # "bybit_connection", "registry"
    status: str              # "healthy", "degraded", "down"
    health_score: int        # 0-100; 90+ healthy, 70-89 degraded, <70 down
    component: str
    detail: str | None
    timestamp: datetime
```

`health_score` agregat dari sub-metric component — connection uptime, reconnect count, event lag.

Dipublish oleh ExchangeConnection (connection_status, uptime, reconnect_count) dan komponen lain.

### OBS-003: AlertEvent (placeholder)

```python
@dataclass
class AlertEvent:
    source: str
    severity: str            # "warning", "critical"
    rule: str                # "bybit_disconnected_60s"
    message: str
    timestamp: datetime
```

Belum diimplementasikan di V1. Framework threshold engine di V2.

Semua OBS event didefinisikan di `src/observability/events.py` — bukan di `src/market_data/`.

## Historical Retention

| Data | Retention | Storage | Alasan |
|------|-----------|---------|--------|
| Connection status | 7 days | Ring buffer + snapshot | Uptime trend cukup 7d |
| Events/sec | 24 hours | Ring buffer | Real-time only |
| Queue depth | 24 hours | Ring buffer | Real-time only |
| Feature freshness | 7 days (V2) | Ring buffer | Snapshot cukup |
| Attention scores | 1 hour (V3) | Ring buffer | Volatile |
| Opportunity queue | Current state only | In-memory | Snapshot driven |

V1 in-memory ring buffer. Retention enforced via TTL cleanup (maxlen). No DB until Grafana/Prometheus migration.

## Alerting (placeholder)

V2 Alert Engine. Not implemented in V1, but contract reserved:

- **Bybit disconnected > 60s** — HealthEvent(status="down") → OBS-003
- **Feature freshness < 90%** — MetricsEvent → OBS-003 (V2)
- **Queue depth > threshold** — MetricsEvent → OBS-003 (V3)
- **Attention leaderboard unchanged > 5 min** — HealthEvent(status="degraded") (V3)

## Replay Compatibility

**Observability data tidak ikut direplay.**

Pipeline replay replay semua event dari Event Store. Observability diregenerasi dari replay — bukan disimpan sebagai source of truth. Alasan:

1. Observability metrics hanya meaningful untuk real-time window
2. Replay sudah punya semua event untuk regenerate metrics
3. Storage observability tidak perlu durable/scalable

## Dashboard Versioning

| Version | Tahap | Producer | Fitur |
|---------|-------|----------|-------|
| **V1** | ADR-012 implement | Connection + Registry | System status, symbol explorer |
| **V2** | ADR-004 Feature Store | EventBus, FeatureStore | Events/sec, latency, feature freshness, **Pipeline View** (React Flow — tiap stage: TPS, latency, queue depth, health) |
| **V3** | ADR-006/007 Breadth+Attention | Breadth, Attention, Tier | Attention board, heat map, queue depth |
| **V4** | ADR-008/009/010 Tier+FQ+Edge | FocusQueue, EdgeEngine | Queue view, edge signal count |
| **V5** | ADR-011 Opportunity | OpportunityEngine | Situation view, urgency panel |
| **V6** | Post-pipeline | TradingEngine | PnL, orders, positions, equity curve |

Setiap versi backward-compatible. API tambah endpoint, gak ubah yang existing.

### V2 (during ADR-004 Feature Store)

```
- Feature freshness per symbol
- Feature computation latency
- Event throughput per stage
- Event lag per exchange (event_lag_ms)
- Stage watermark (stage_watermark per component)
- Stage-level health
- Pipeline View — React Flow diagram dengan tiap stage sebagai node.
  Setiap node menampilkan: TPS, latency, queue depth, health status.
  Warna node: hijau (sehat), kuning (tertunda), merah (error).
```

### V3 (during ADR-007 Attention)

```
- Attention leaderboard
- Heat map per sector
- Tier distribution
- Queue depth (Focus Queue)
```

### V4 (during ADR-011 Opportunity)

```
- Active special situations
- Opportunity queue view
- Urgency distribution
- Edge signal counts
```

## Non-Goals

- **Not a trading dashboard** — no PnL, orders, positions, equity curve
- **Not APM** — no distributed tracing, no profiling. Pure pipeline observability
- **Not persistent** — ring buffer dengan TTL. Riwayat panjang nanti Pakai DB terpisah
- **Not a replacement for logs** — `structured` JSON logging tetap jalan parallel

## Consequences

### Positive

- Setiap komponen baru tinggal publish event ke Metrics Bus
- Dashboard bisa verifikasi implementasi sesuai ADR tanpa baca log
- Bottleneck langsung terlihat sebelum edge engine aktif
- Arsitektur terpisah → observability gagal gak bikin pipeline mati

### Negative

- Overhead kode tambahan per stage (publish metrics event)
- Ring buffer terbatas — data lama hilang kalau dashboard mati lama
- V1 dashboard sebagian besar statis karena belum ada producer throughput

## Design Answers

| Question | Answer |
|----------|--------|
| Kenapa bukan Grafana + Prometheus? | Infra tambahan. Untuk V1 in-memory cukup. Migrasi ke Prometheus nanti |
| Kenapa Metrics Bus pisah dari pipeline bus? | Pipeline bus bisa blockage. Metrics bus gak boleh blocking |
| Kenapa dashboard di repo sama? | Satu developer. Pisah repo nanti saat tim > 1 |
| Connection status udah di EventBus kenapa simpan ulang? | Ring buffer serve API tanpa blocking pipeline bus |
| Kenapa OBS event di folder terpisah? | Observability event bukan domain market data. Bisa dihapus independen |
| Observability ikut replay? | Tidak. Diregenerasi dari replay |
| Retention berapa lama? | 7d connection, 24h metrics, current state untuk queue/scores |
| Alert engine kapan? | V2, bersamaan Feature Store |
