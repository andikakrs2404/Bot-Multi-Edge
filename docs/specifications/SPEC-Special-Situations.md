# SPEC-Special-Situations

**Status:** DRAFT  
**Date:** 2026-07-27  
**Owner:** Lead Architect  

---

## Purpose

Definisi Special Situation Pipeline — jalur paralel yang bypass Attention Engine dan masuk langsung ke Opportunity Queue. Special Situation adalah **Attention Override Mechanism**, bukan edge. Edge tetap dieksekusi oleh Edge Engine setelah symbol masuk Opportunity Queue.

```
Special Situation Detected
    │
    ▼
OpportunityCandidate
    │
    ▼
Opportunity Queue
    │
    ▼
Edge Engine (evaluates normally)
```

## Principles

1. **Special Situation ≠ Edge.** Situation hanya membuka akses ke Opportunity Queue. Edge tetap dieksekusi oleh Edge Engine.
2. **Bypass Attention.** Situation tidak perlu heat_score tinggi. Cukup terdeteksi.
3. **Expiration wajib.** Setiap situation punya masa berlaku. Setelah expired, symbol kembali ke pipeline normal.
4. **Cooldown.** Mencegah spam — situation yang sama tidak dapat trigger ulang dalam cooldown period.
5. **Priority.** CRITICAL > HIGH > MEDIUM > LOW. Priority menentukan posisi di Opportunity Queue.

## Situation Registry

Setiap situation wajib terdaftar dengan kontrak berikut:

```yaml
situation_id: SS001
name: New Listing
priority: HIGH
active_duration: 24h
cooldown_duration: 24h
owner: SpecialSituationEngine
```

### Registry Index

| ID | Name | Priority | Active Duration | Cooldown | V1? |
|----|------|----------|----------------|----------|-----|
| SS001 | New Listing | HIGH | 24h | 24h | ✅ |
| SS002 | OI Explosion | HIGH | 30m | 15m | ✅ |
| SS003 | Liquidation Cascade | CRITICAL | 30m | 15m | ✅ |
| SS004 | Funding Extreme | HIGH | 6h | 6h | ✅ |
| SS005 | Leader Follower | MEDIUM | 30m | 30m | ❌ V2 |
| SS006 | Sector Rotation | MEDIUM | 4h | 4h | ❌ V2 |
| SS007 | Volume Anomaly | MEDIUM | 15m | 10m | ❌ V2 |
| SS008 | News Shock | LOW | 2h | 4h | ❌ V3 |
| SS009 | Spread Dislocation | LOW | 10m | 10m | ❌ V3 |

## Situation Lifecycle

```
DETECTED ──► ACTIVE ──► MONITORING ──► EXPIRED
  │            │            │
  │            ▼            ▼
  │      In Opportunity   Still in queue but
  │      Queue, Edge      lower priority;
  │      Engine runs      will be removed if
  │                       queue is full
  ▼
Initial trigger.
OpportunityCandidate created.
```

| Phase | Description | Edge Engine behavior |
|-------|-------------|---------------------|
| DETECTED | Situation just triggered | OpportunityCandidate created, enqueued |
| ACTIVE | In Opportunity Queue | Edge Engine evaluates normally |
| MONITORING | Past peak, still in queue | Lower priority, may be evicted |
| EXPIRED | Removed from queue | Symbol returns to normal pipeline |

## Detection Contract

Semua detector wajib mengikuti kontrak:

```python
def detect(symbol_state: SymbolState) -> SituationEvent | None:
    """
    Evaluate one symbol for this situation.
    Returns SituationEvent if triggered, None otherwise.
    """
```

### SituationEvent

```python
@dataclass
class SituationEvent:
    symbol: str
    exchange: str
    situation_id: str
    urgency_score: float          # 0-100, how strong is this trigger
    priority: str                 # CRITICAL | HIGH | MEDIUM | LOW
    expires_at: datetime
    metadata: dict                # trigger-specific data (price, volume, reason)
    detected_at: datetime
```

### OpportunityCandidate (Queue Entry)

```python
@dataclass
class OpportunityCandidate:
    symbol: str
    exchange: str
    situation_id: str
    urgency_score: float
    priority: str
    expires_at: datetime
    detected_at: datetime
    enqueued_at: datetime
```

## Situation Details (V1)

### SS001 — New Listing

```yaml
situation_id: SS001
name: New Listing
priority: HIGH
active_duration: 24h
cooldown_duration: 24h

detection:
  source: Symbol Registry (symbol_added event)
  trigger: New contract listed on exchange
  cooldown: Per symbol, per exchange (symbol can't be "new listed" twice)

expiration:
  type: timed
  duration: 24h
  after: first detection

opportunity_queue:
  eviction_rank: last_evicted    # preserved over lower-priority entries
```

**Notes:** New listing langsung masuk Opportunity Queue tanpa perlu deteksi tambahan. Setelah 24h, symbol dirilis ke pipeline normal (Stage 1 Fast Screening).

---

### SS002 — OI Explosion

```yaml
situation_id: SS002
name: OI Explosion
priority: HIGH
active_duration: 30m
cooldown_duration: 15m

detection:
  source: Feature Store (F002 OI Expansion)
  trigger: OI expansion > P99 (within universe, 30d window)
  window: 5m rolling
  min_symbol_age: 1h (skip new listing — they already in OQ)

expiration:
  type: timed
  duration: 30m
  after: last trigger

opportunity_queue:
  eviction_rank: high
```

**Notes:** OI explosion > P99 is rare and often precedes major moves. Gets fast-tracked to Edge Engine.

---

### SS003 — Liquidation Cascade

```yaml
situation_id: SS003
name: Liquidation Cascade
priority: CRITICAL
active_duration: 30m
cooldown_duration: 15m

detection:
  source: Event Bus (liquidation events)
  trigger: 3+ liquidations on same symbol within 5m window
  min_total_size: $500K
  cooldown: Per symbol

expiration:
  type: timed
  duration: 30m
  after: last liquidation event

opportunity_queue:
  eviction_rank: never_evicted   # critical — preserved even if OQ full
```

**Notes:** CRITICAL priority. Never evicted from Opportunity Queue. Liquidation cascade often marks local top/bottom.

---

### SS004 — Funding Extreme

```yaml
situation_id: SS004
name: Funding Extreme
priority: HIGH
active_duration: 6h
cooldown_duration: 6h

detection:
  source: Feature Store (F006 Funding Rate)
  trigger: Funding rate > 0.05% (longs paying extreme) OR < -0.05% (shorts paying extreme)
  window: Per funding interval (1h)
  cooldown: Per symbol, per exchange

expiration:
  type: timed
  duration: 6h
  after: last funding trigger

opportunity_queue:
  eviction_rank: high
```

**Notes:** Funding extreme signals crowded positioning. Reversal edge (E002) will evaluate while symbol is in OQ.

## Detection Pipeline

```
Event Bus (raw events)
    │
    ▼
Situation Detectors (one per situation_id)
    │
    ├── SS001: listen symbol_added
    ├── SS002: read F002 from Feature Store
    ├── SS003: listen liquidation events
    ├── SS004: read F006 from Feature Store
    │
    ▼
SituationEvent (if triggered)
    │
    ├── Check cooldown (skip if still in cooldown)
    ├── Check expiration (skip if same situation already active for symbol)
    │
    ▼
OpportunityCandidate
    │
    ▼
Opportunity Queue
```

All detectors run in parallel. Independent of main pipeline cycle.

## Opportunity Queue Integration

Detail queue behavior in ADR-009. Here: situation-specific rules.

| Priority | Eviction rank | Max concurrent per symbol |
|----------|---------------|--------------------------|
| CRITICAL | Never evicted | 1 (can't have two critical situations same symbol? actually can — liquidation + OI explosion) |
| HIGH | Last evicted | 2 |
| MEDIUM | Evicted before HIGH | 1 |
| LOW | First evicted | 1 |

**Multiple situations per symbol:** Allowed. Symbol can be in Opportunity Queue for both SS002 (OI Explosion) and SS003 (Liquidation Cascade). Edge Engine evaluates symbol once per tick regardless of how many situations triggered it.

## Expiration & Cleanup

| Trigger | Action |
|---------|--------|
| `expires_at` reached | Remove from Opportunity Queue. Emit `situation_expired` event |
| Symbol delisted | Remove immediately |
| Edge Engine evaluates | Not removed — stays until expired (re-evaluated next tick if still in OQ) |
| Queue overflow | Lowest-priority, oldest-expiring entry evicted (see ADR-009 eviction policy) |

## Cooldown Table

| Situation | Cooldown | Rationale |
|-----------|----------|-----------|
| SS001 New Listing | 24h | Per symbol, only listed once |
| SS002 OI Explosion | 15m | OI can spike multiple times |
| SS003 Liquidation Cascade | 15m | Cascades can repeat |
| SS004 Funding Extreme | 6h | Funding settles every 1h |

Cooldown applied per (symbol, situation_id). After cooldown expires, situation can retrigger.

## Metrics

Per situation:

| Metric | Description |
|--------|-------------|
| `detected_count` | Times this situation triggered |
| `enqueued_count` | Times entry added to OQ (after cooldown check) |
| `expired_count` | Times entry expired naturally |
| `evicted_count` | Times entry evicted due to overflow |
| `avg_urgency_score` | Average urgency on detection |
| `avg_active_duration` | How long entries stayed in OQ |

## References

- ADR-003: Screener Architecture (Special Situation Pipeline)
- ADR-009: Focus Queue (Opportunity Queue)
- ADR-010: Edge Framework
- FEATURE-Registry (F002, F006)
