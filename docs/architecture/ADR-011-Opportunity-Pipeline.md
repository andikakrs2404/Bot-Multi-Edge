# ADR-011: Opportunity Pipeline

**Status:** DRAFT  
**Date:** 2026-07-27  
**Author:** Lead Architect  
**Deciders:** Lead Architect  

---

## Context

Special Situation Pipeline (SPEC-Special-Situations) mendefinisikan **apa itu** special situation — registry, trigger, lifecycle. Tapi belum mendefinisikan **bagaimana runtime bekerja** — detector scheduling, enqueue/dequeue, persistence, replay, attribution.

Dokumen ini adalah runtime architecture untuk jalur paralel:

```
Market Data / Feature Store / Event Bus
    │
    ▼
Detector Scheduler
    │
    ├── SS001 New Listing (60s)
    ├── SS002 OI Explosion (5s)
    ├── SS003 Liquidation Cascade (realtime)
    └── SS004 Funding Extreme (5m)
           │
           ▼
Opportunity Engine
    │
    ├── Cooldown check
    ├── Expiration check
    ├── Urgency score calculation
    ├── Enqueue to Opportunity Queue
    └── Emit OpportunityEvent
           │
           ▼
Opportunity Queue (priority queue)
    │
    ├── Drained before Focus Queue
    └── Edge Engine evaluates
           │
           ▼
Opportunity Store (persistence + attribution)
```

## Decision

Build **Opportunity Pipeline** sebagai subsystem runtime terpisah dengan 4 komponen: Detector Scheduler, Opportunity Engine, Opportunity Queue (shared with ADR-009), Opportunity Store.

## Architecture

```
Event Bus
    │
    ▼
Detector Scheduler
  (runs detectors on their schedule)
    │
    ▼
For each detector that triggers:
    │
    ▼
OpportunityEngine.process(situation_event)
    │
    ├── 1. Check cooldown (skip if active per symbol+situation)
    ├── 2. Check expiration (skip if same situation already active)
    ├── 3. Calculate urgency_score (0-100)
    ├── 4. Create OpportunityCandidate
    ├── 5. Enqueue to Opportunity Queue
    └── 6. Persist OpportunityEvent to Store
           │
           ▼
Edge Engine drains Opportunity Queue
(before Focus Queue, per ADR-009)
```

### Components

| Component | Role |
|-----------|------|
| **Detector Scheduler** | Runs each detector on its configured interval. Realtime detectors subscribe to Event Bus directly |
| **Opportunity Engine** | Receives SituationEvent, validates cooldown/expiration, calculates urgency, enqueues |
| **Opportunity Queue** | Priority queue (shared with ADR-009). Drained before Focus Queue |
| **Opportunity Store** | Persists all OpportunityEvents for replay, attribution, metrics |

## Detector Scheduler

Each situation detector runs on its own schedule:

| Situation | Schedule | Type | Rationale |
|-----------|----------|------|-----------|
| SS001 New Listing | Every 60s | Poll Symbol Registry | New listings rare, 60s latency acceptable |
| SS002 OI Explosion | Every 5s | Poll Feature Store | OI changes fast, 5s catches spikes |
| SS003 Liquidation Cascade | **Realtime** | Event Bus subscription | Must catch every liquidation event |
| SS004 Funding Extreme | Every 5m | Poll Feature Store | Funding settles every 1h, 5m more than enough |
| SS005 Leader Follower | Every 10s (V2) | Poll Attention Store | Leader moves propagate in seconds |
| SS006 Sector Rotation | Every 60s (V2) | Poll Breadth Store | Rotation detected over minutes |

```python
@scheduler.interval(seconds=5)
def detect_oi_explosion():
    symbols = feature_store.query_by_feature("F002", min_val=99)  # > P99
    for symbol in symbols:
        event = SituationEvent(
            symbol=symbol.symbol,
            situation_id="SS002",
            urgency_score=calculate_urgency(symbol),
            ...
        )
        opportunity_engine.process(event)

@cheduler.realtime(event_type="liquidation")
def detect_liquidation_cascade(event):
    cache.add(event.symbol, event)  # rolling 5m window
    if cache.count(event.symbol) >= 3 and cache.total_size(event.symbol) > 500_000:
        situation = SituationEvent(...)
        opportunity_engine.process(situation)
```

### Detector Contract

```python
@dataclass
class Detector:
    situation_id: str
    schedule_type: Literal["interval", "realtime"]
    interval_seconds: int | None    # None for realtime
    source: Literal["event_bus", "feature_store", "symbol_registry", "breadth_store"]
    enabled: bool

    def detect(self) -> list[SituationEvent]:
        """Run detection logic. Return triggered events."""
        ...
```

## Opportunity Engine

Core logic untuk memproses SituationEvent menjadi OpportunityCandidate.

```python
@dataclass
class OpportunityEngine:
    cooldown_tracker: CooldownTracker
    expiration_tracker: ExpirationTracker
    queue: OpportunityQueue
    store: OpportunityStore

    def process(self, event: SituationEvent) -> OpportunityCandidate | None:
        # 1. Cooldown check
        if self.cooldown_tracker.is_active(event.symbol, event.situation_id):
            logger.debug(f"Cooldown active: {event.symbol} {event.situation_id}")
            return None

        # 2. Expiration check (same situation already active for this symbol?)
        if self.expiration_tracker.is_active(event.symbol, event.situation_id):
            logger.debug(f"Situation already active: {event.symbol} {event.situation_id}")
            return None

        # 3. Calculate urgency score
        urgency = self.calculate_urgency(event)

        # 4. Create candidate
        candidate = OpportunityCandidate(
            symbol=event.symbol,
            exchange=event.exchange,
            situation_id=event.situation_id,
            urgency_score=urgency,
            priority=event.priority,
            expires_at=event.expires_at,
            detected_at=event.detected_at,
            enqueued_at=datetime.utcnow()
        )

        # 5. Enqueue
        self.queue.enqueue(candidate)

        # 6. Persist
        self.store.record(event, candidate)

        # 7. Start cooldown
        self.cooldown_tracker.start(event.symbol, event.situation_id)

        return candidate
```

### Urgency Score

0-100. Menentukan posisi dalam Opportunity Queue. Semakin tinggi, semakin cepat diproses Edge Engine.

```python
def calculate_urgency(self, event: SituationEvent) -> float:
    """
    Base urgency from situation type + dynamic modifiers.
    """
    base = {
        "SS001": 50,   # New listing — moderate urgency
        "SS002": 80,   # OI explosion — high
        "SS003": 95,   # Liquidation cascade — critical
        "SS004": 70,   # Funding extreme — high
    }.get(event.situation_id, 50)

    # Dynamic modifiers
    modifiers = 0
    if event.metadata.get("liquidation_size", 0) > 1_000_000:
        modifiers += 10  # Big liquidation → higher urgency
    if event.metadata.get("oi_change_pct", 0) > 30:
        modifiers += 10  # Extreme OI spike
    if event.priority == "CRITICAL":
        modifiers += 15

    return min(base + modifiers, 100)
```

### Cooldown Tracker

```python
@dataclass
class CooldownTracker:
    cooldowns: dict[tuple[str, str], datetime]  # (symbol, situation_id) → expires_at

    def is_active(self, symbol: str, situation_id: str) -> bool:
        key = (symbol, situation_id)
        if key not in self.cooldowns:
            return False
        return datetime.utcnow() < self.cooldowns[key]

    def start(self, symbol: str, situation_id: str):
        duration = COOLDOWN_DURATIONS.get(situation_id, 3600)  # default 1h
        self.cooldowns[(symbol, situation_id)] = datetime.utcnow() + timedelta(seconds=duration)
```

### Expiration Tracker

```python
@dataclass
class ExpirationTracker:
    active: dict[tuple[str, str], datetime]  # (symbol, situation_id) → expires_at

    def is_active(self, symbol: str, situation_id: str) -> bool:
        key = (symbol, situation_id)
        if key not in self.active:
            return False
        if datetime.utcnow() > self.active[key]:
            del self.active[key]
            return False
        return True

    def register(self, symbol: str, situation_id: str, expires_at: datetime):
        self.active[(symbol, situation_id)] = expires_at
```

## Opportunity Queue

Queue terpisah dengan prioritas di atas Focus Queue. Detail queue behavior di ADR-009. Di sini: runtime integration.

### Queue Entry

```python
@dataclass(order=True)
class OpportunityCandidate:
    urgency_score: float          # sort key (descending)
    priority_order: int           # secondary sort: CRITICAL=0, HIGH=1, MEDIUM=2, LOW=3
    symbol: str
    exchange: str
    situation_id: str
    priority: str
    expires_at: datetime
    detected_at: datetime
    enqueued_at: datetime
```

### Sort Order

```
1. urgency_score descending (highest urgency first)
2. priority_order ascending (CRITICAL before HIGH)
3. enqueued_at ascending (older entries first, FIFO tiebreaker)
```

### Eviction (Overflow)

When queue exceeds max_size (20):

```
1. Find entries with lowest urgency_score
2. Among those, lowest priority
3. Among those, oldest enqueued_at
4. Evict that entry
```

Per SPEC-Special-Situations: **CRITICAL entries (SS003) are never evicted.** If queue is full of CRITICAL entries, enqueue fails and logs warning.

### Drain

Edge Engine drains Opportunity Queue completely before touching Focus Queue. Per ADR-009:

```python
# In Edge Engine tick:
while not opportunity_queue.is_empty():
    candidate = opportunity_queue.dequeue()
    evaluate_symbol(candidate.symbol, source="opportunity")

# Then drain Focus Queue tiers...
```

## Persistence & Replay

### OpportunityEvent (stored)

```json
{
  "event_id": "opp-20260727-120100-TAO",
  "symbol": "TAOUSDT",
  "exchange": "BINANCE",
  "situation_id": "SS002",
  "priority": "HIGH",
  "urgency_score": 88,
  "detected_at": "2026-07-27T12:01:00.000Z",
  "enqueued_at": "2026-07-27T12:01:00.050Z",
  "expires_at": "2026-07-27T12:31:00.000Z",
  "evicted_at": null,
  "evaluated_at": "2026-07-27T12:01:00.100Z",
  "edge_results": {
    "E001": { "direction": "LONG", "score": 88 },
    "E003": { "direction": "LONG", "score": 72 }
  }
}
```

### Event Store

All OpportunityEvents persisted to append-only log. Enables:

- **Replay:** Reconstruct Opportunity Queue state at any point in time
- **Attribution:** Link trades back to the situation that triggered them
- **Metrics:** P&L per situation, detection frequency, avg urgency
- **Post-mortem:** Why was this symbol in OQ? When was it evicted?

### Replay Mode

During replay, Opportunity Engine reads from stored events instead of running detectors.

```python
# Normal mode:
detector_scheduler.run()
opportunity_engine.process(event)

# Replay mode:
for stored_event in opportunity_store.get_events_between(start, end):
    opportunity_engine.process(stored_event, replay=True)
```

## Promotion History

Per symbol per situation:

```python
@dataclass
class OpportunityPromotion:
    symbol: str
    situation_id: str
    detected_at: datetime
    enqueued_at: datetime
    evaluated_at: datetime | None
    evicted_at: datetime | None
    expired_at: datetime | None
    urgency_score: float
    edge_count: int
    signal_generated: bool
```

Stored in Opportunity Store. Queryable for research.

## Opportunity Attribution

Trade → Situation linkage. Setiap AggregatedSignal dari Edge Engine yang berasal dari Opportunity Queue membawa `source: "opportunity"` dan `situation_id`.

```json
{
  "signal_id": "sig-20260727-120100-TAOUSDT",
  "source": "opportunity",
  "situation_id": "SS002",
  "symbol": "TAOUSDT",
  "direction": "LONG",
  "aggregated_score": 81,
  "contributing_edges": ["E001", "E003"]
}
```

Later, P&L analysis:

```
Profit by Situation:
  SS002 OI Explosion:    +$1,240 (8 trades)
  SS003 Liq Cascade:     +$890  (3 trades)
  SS004 Funding Extreme: +$420  (2 trades)
  SS001 New Listing:     +$150  (5 trades)
```

## Opportunity Metrics

Per situation (from Opportunity Store):

| Metric | Description |
|--------|-------------|
| `detected_count` | Times this situation triggered |
| `enqueued_count` | Times entry added to OQ (after cooldown) |
| `evaluated_count` | Times Edge Engine evaluated |
| `signal_count` | Times evaluation produced a signal |
| `evicted_count` | Times entry evicted before Edge eval |
| `expired_count` | Times entry expired naturally |
| `avg_urgency` | Average urgency score |
| `avg_latency_enqueue_ms` | Time from detect → enqueue |
| `avg_latency_eval_ms` | Time from enqueue → Edge eval |

Global metrics:

| Metric | Description |
|--------|-------------|
| `oq_depth` | Current OQ size |
| `oq_overflow_events` | Times OQ hit max_size |
| `oq_cooldown_hits` | Times cooldown blocked detection |

## Config

```yaml
# opportunity_pipeline.yaml (hot-reloadable)
detectors:
  SS001:
    enabled: true
    schedule_interval_s: 60
  SS002:
    enabled: true
    schedule_interval_s: 5
  SS003:
    enabled: true
    schedule_type: realtime
  SS004:
    enabled: true
    schedule_interval_s: 300

opportunity_queue:
  max_size: 20
  sort_by: [urgency_score desc, priority asc, enqueued_at asc]
  never_evict_situations: [SS003]

cooldown_default_s: 3600
```

## Non-Goals (V1)

- ML-based urgency scoring (rule-based in V1)
- Cross-symbol opportunity correlation (e.g. BTC liquidation → ETH opportunity)
- Opportunity queue priority boosting (all CRITICAL equal)

## Consequences

**Positive:**
- Detector scheduling separates detection frequency from main pipeline cycle
- Urgency score enables fine-grained prioritization within Opportunity Queue
- Persistence enables exact replay and attribution
- Promotion history enables research: which situations actually produce signals?
- Attribution enables P&L-by-situation analysis, not just by-edge
- Cooldown + expiration prevent spam and stale entries

**Negative:**
- Separate scheduler adds complexity (each detector has own interval)
- Urgency scoring is rule-based — may need tuning per market regime
- Persistence adds write load on every detection
- Attribution trace requires Edge Engine to propagate situation_id through to AggregatedSignal

## References

- SPEC-Special-Situations (situation registry, triggers, lifecycle)
- ADR-003: Screener Architecture (parallel path)
- ADR-009: Focus Queue (Opportunity Queue integration)
- ADR-010: Edge Framework (signal attribution)
