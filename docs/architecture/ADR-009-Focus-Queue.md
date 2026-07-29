# ADR-009: Focus Queue

**Status:** DRAFT  
**Date:** 2026-07-27  
**Author:** Lead Architect  
**Deciders:** Lead Architect  

---

## Context

Tier Assignment (ADR-008) menentukan tier mana symbol berada. Tapi Edge Engine butuh **urutan eksekusi** — symbol mana yang diproses duluan dalam setiap siklus. Focus Queue adalah antrian prioritas antara Tier Assignment dan Edge Engine.

```
Tier Assignment
    │
    ▼
Focus Queue
    │
    ├──► Tier A symbols (drained first)
    ├──► Tier B symbols (drained second)
    ├──► Tier C symbols (drained third)
    └──► Tier D symbols (periodic)
           │
           ▼
Edge Engine
```

**Parallel:** Opportunity Queue dari Special Situation Pipeline — drained BEFORE Focus Queue.

## Decision

Build **Focus Queue** sebagai priority queue dengan strict tier ordering. Opportunity Queue memiliki prioritas lebih tinggi dari Tier A.

## Queue Structure

```
Edge Engine drain order:

1. Opportunity Queue (from Special Situation)
2. Tier A (top 20 — every tick)
3. Tier B (top 50 — every 5 ticks)
4. Tier C (top 200 — every 30 ticks)
5. Tier D (universe — on demand / periodic scan)
```

### Queue Properties

| Property | Value |
|----------|-------|
| Ordering | Strict tier priority (A > B > C > D) |
| Within tier | **heat_score descending** (highest urgency first) |
| Tiebreaker | attention_score descending |
| Starvation protection | Tier B/C get guaranteed minimum cycles even if A never empty |
| Persistence | Queue state persisted for replay |
| Max total queued | 270 (A=20 + B=50 + C=200) |

## Drain Policy

### Tick Allocation

Each tick, Edge Engine processes:

| Source | Max per tick | Notes |
|--------|-------------|-------|
| Opportunity Queue | All pending | Drained completely before anything else |
| Tier A | All 20 | Every tick |
| Tier B | 10 | Round-robin across 50 |
| Tier C | 7 | Round-robin across 200 |
| Tier D | 0 | On-demand only |

### Round-Robin Within Tier

Tier B dan C tidak bisa diproses semua setiap tick. Round-robin memastikan semua symbol dalam tier mendapat giliran. Dalam setiap batch, symbol diurutkan **heat_score descending** — bukan FIFO.

```
Tier B (50 symbols, sorted by heat desc):
Tick 1:  positions 1-10 (highest heat in B)
Tick 2:  positions 11-20
Tick 3:  positions 21-30
Tick 4:  positions 31-40
Tick 5:  positions 41-50
Repeat every 5 ticks

Tier C (200 symbols, sorted by heat desc):
Tick 1:  positions 1-7
Tick 2:  positions 8-14
...
Tick 29: positions ?-200
Repeat every ~30 ticks
```

### Starvation Protection

Jika Tier A selalu penuh dan Opportunity Queue selalu ada, Tier B/C bisa kelaparan.

**Rule:** Every 10 ticks, at least 1 tick reserved for Tier B/C even if A/OQ pending.

## Queue Operations

### Enqueue

Symbol masuk queue via Tier Assignment:

```json
{
  "operation": "enqueue",
  "symbol": "TAOUSDT",
  "tier": "A",
  "heat_score": 92,
  "attention_score": 88,
  "timestamp": "2026-07-27T12:01:00.000Z"
}
```

**Trigger:** Tier assignment change, new symbol added, special situation detected.

### Dequeue (pop)

Edge Engine meminta symbol berikutnya:

```json
{
  "operation": "dequeue",
  "tier": "A",
  "symbol": "BTCUSDT",
  "position": 1,
  "remaining_in_tier": 19
}
```

### Reorder

Ketika Tier Assignment berubah (setiap 60s), queue di-rebuild dari tier assignment snapshot. Urutan FIFO dalam tier di-reset — semua symbol dalam tier dianggap baru masuk.

### Remove

Symbol dihapus dari semua queue tiers saat:

- `symbol_removed` event
- Demotion to Tier D (optional — Tier D tidak di-queue aktif)

### Requeue

Setelah symbol diproses Edge Engine, symbol **tidak langsung di-dequeue permanent**. Focus Queue adalah scheduler round-robin — symbol tetap di queue untuk siklus berikutnya, kecuali di-demote oleh Tier Assignment.

```
Edge Engine processes TAO (Tier A)
    │
    ├── Signal ditemukan? → Tetap di queue, evaluasi next tick
    └── No signal? → Tetap di queue, evaluasi next tick

Hanya dihapus jika:
- Demotion ke tier lebih rendah (pindah ke queue tier baru)
- Demotion ke Tier D (keluar dari queue aktif)
- symbol_removed event
```

## Symbol Cooldown

Mencegah symbol yang baru diproses langsung masuk queue lagi dalam milidetik.

```yaml
cooldown:
  tier_a_seconds: 5
  tier_b_seconds: 15
  tier_c_seconds: 60
  tier_d_seconds: 300
```

Setelah Edge Engine selesai mengevaluasi symbol, cooldown timer mulai. Symbol tidak akan di-dequeue lagi sampai cooldown expired. Cooldown dihitung dari **akhir evaluasi**, bukan dari enqueue.

Cooldown dilewati jika:
- Opportunity Queue entry (special situation override)
- heat_score naik > 20 poin sejak evaluasi terakhir

## Edge Budget per Tier

Tidak semua edge perlu jalan di semua tier. Edge Budget mengontrol berapa banyak edge yang dieksekusi per symbol per tier.

| Tier | Edge budget | Notes |
|------|-------------|-------|
| A | All edges (20+) | Full evaluation |
| B | High-priority edges only (~10) | Skip experimental / heavy edges |
| C | Lightweight edges only (~5) | Only cheap statistical edges |
| D | 0 | On-demand only |

Edge priority classification done in EDGE-Registry (see ADR-010).

**Rationale:** Tier B = 50 symbols × 10 edges = 500 evaluations per 5 ticks. Tier C = 200 × 5 edges = 1000 per 30 ticks. Without budget, B+C would cost more than A.

## Opportunity Queue

Queue terpisah untuk Special Situation.

| Property | Value |
|----------|-------|
| Priority | Higher than Tier A |
| Drain | Completely emptied before Focus Queue |
| Source | Special Situation Pipeline (ADR-003) |
| Max size | 20 (configurable) |
| Overflow | Evict lowest-urgency entry (preserve NEW_LISTING, LIQUIDATION_CASCADE) |

Priority tiers within Opportunity Queue:

| Priority | Type | Eviction rank |
|----------|------|---------------|
| Critical | LIQUIDATION_CASCADE, EXCHANGE_INCIDENT | Never evicted |
| High | NEW_LISTING, FUNDING_EXTREME | Last evicted |
| Medium | MASSIVE_OI_SPIKE | Evicted first |

```json
{
  "queue": "opportunity",
  "symbol": "NEWUSDT",
  "reason": "NEW_LISTING",
  "priority": "high",
  "enqueued_at": "2026-07-27T12:01:00.000Z"
}
```

## Queue State Persistence

Queue state disimpan untuk replay:

```json
{
  "queue_snapshot_id": "fq-20260727-120100",
  "timestamp": "2026-07-27T12:01:00.000Z",
  "opportunity_queue": ["NEWUSDT"],
  "tier_a": ["BTCUSDT", "TAOUSDT", "ETHUSDT"],
  "tier_b": ["RNDRUSDT", "SOLUSDT"],
  "tier_c": ["FETUSDT", "AKTUSDT"],
  "tier_d": [],
  "tick_counter": 1523,
  "b_round_robin_index": 3,
  "c_round_robin_index": 15
}
```

## Queue Metrics

Untuk monitoring dashboard:

| Metric | Description | Source |
|--------|-------------|--------|
| `queue_depth_a` | Current symbols in Tier A queue | Snapshot |
| `queue_depth_b` | Current symbols in Tier B | Snapshot |
| `queue_depth_c` | Current symbols in Tier C | Snapshot |
| `queue_depth_oq` | Current symbols in Opportunity Queue | Snapshot |
| `avg_wait_time_a` | Average time symbol spends in Tier A before first dequeue | Rolling 10min |
| `avg_wait_time_b` | Same for Tier B | Rolling 10min |
| `avg_wait_time_c` | Same for Tier C | Rolling 10min |
| `cooldown_hits` | How often cooldown blocks a dequeue | Counter |
| `oq_evictions` | How often Opportunity Queue entries evicted | Counter |
| `starvation_events` | How often starvation protection triggered | Counter |

## Config

```yaml
# focus_queue.yaml (hot-reloadable)
tiers:
  A:
    max_per_tick: 20
    drain_every_tick: true
    edge_budget: all                 # which edges run on this tier
  B:
    total: 50
    max_per_tick: 10
    drain_every_n_ticks: 5
    edge_budget: high_priority
  C:
    total: 200
    max_per_tick: 7
    drain_every_n_ticks: 30
    edge_budget: lightweight
  D:
    enabled: false
    scan_interval_cycles: 100
    edge_budget: none

opportunity_queue:
  max_size: 20
  drain_before_focus: true

starvation_protection:
  reserved_tick_every_n: 10

cooldown:
  tier_a_seconds: 5
  tier_b_seconds: 15
  tier_c_seconds: 60
  tier_d_seconds: 300

within_tier_sort: heat_score_desc    # heat_score_desc | heat_score_asc | attention_score_desc | fifo
```

## Consumer Map

| Consumer | Reads | What |
|----------|-------|------|
| Stage 8: Edge Engine | Dequeue next symbol | Evaluate symbol against all edges |
| Dashboard UI | Queue state, round-robin progress | Human monitoring |
| Replay Engine | Queue snapshot | Reconstruct past state |

## Non-Goals (V1)

- Dynamic queue resizing based on market volatility
- Cross-exchange queue merging
- Cross-tier priority boosting (symbol in B never preempts A)
- Edge budget auto-tuning (budget per tier is static via config)

## Consequences

**Positive:**
- Strict tier priority ensures high-signal symbols always processed first
- Opportunity Queue preempts everything — special situations never wait
- heat_score ordering within tier ensures hottest symbol processed first (not FIFO)
- Requeue policy keeps symbol in queue until demoted — no unnecessary re-enqueue
- Cooldown prevents micro-flapping; symbol gets breathing room between evaluations
- Edge budget per tier bounds compute cost (A=all, B=high, C=light)
- Round-robin within tier prevents symbol starvation
- Starvation protection guarantees Tier B/C minimum processing
- Queue persistence enables exact replay
- Queue metrics enable dashboard monitoring

**Negative:**
- heat_score ordering within tier shifts on every attention update — queue must re-sort each tick
- Round-robin adds complexity: tick counter, index tracking, boundary cases on tier change
- Cooldown adds latency — hot symbol must wait 5s even if heat_score jumps again immediately
- Edge budget means some edges never run on Tier B/C — less data for those symbols
- Starvation protection reduces Tier A throughput up to 10%
- Queue rebuild on tier change loses heat_score ordering position within tier

## References

- ADR-003: Screener Architecture (Stage 7: Focus Queue)
- ADR-008: Tier Assignment
- ADR-010: Edge Framework
