# ADR-010: Edge Engine Framework

**Status:** DRAFT  
**Date:** 2026-07-27  
**Author:** Lead Architect  
**Deciders:** Lead Architect  

---

## Context

Pipeline dari Market Data sampai Focus Queue sudah selesai. Sekarang giliran komponen terakhir: **Edge Engine** — tempat semua strategi trading dieksekusi.

Sistem akan menampung 20+ edge strategies. Setiap edge adalah detektor sinyal independen. Edge Engine harus:

- Menjalankan edge sesuai budget per tier (ADR-009)
- Menjamin edge tidak saling mengganggu
- Memastikan semua edge membaca feature dari store (bukan hitung ulang)
- Menghasilkan sinyal teragregasi untuk eksekusi

## Decision

Build **Edge Engine Framework** dengan 3 komponen: Edge Registry, Edge Executor, Signal Aggregator. Setiap edge adalah plugin independen dengan kontrak tetap.

```
Focus Queue → Opportunity Queue
    │               │
    ▼               ▼
Edge Executor
    │
    ├──► E001 OI Breakout
    ├──► E002 Funding Reversal
    ├──► E003 Volume Momentum
    ├──► ...
    └──► E020+ (plugin)
           │
           ▼
Signal Aggregator
    │
    ├──► Consensus signal (multiple edges agree)
    ├──► Standalone signal (single high-confidence edge)
    └──► Conflicting signals (edges disagree → reduce position)
           │
           ▼
Execution Layer
```

## Architecture

```
Dequeue Symbol (from Focus/Opportunity Queue)
    │
    ▼
Edge Executor
    │
    ├── Filter edges by tier budget (A=all, B=high, C=light)
    ├── Check cooldown (skip if not expired)
    ├── Read symbol state from stores (Feature, Normalization, Breadth)
    │
    ▼
For each eligible edge:
    edge.evaluate(symbol_state) → EdgeResult
    │
    ├── Edge score (0-100)
    ├── Direction (LONG / SHORT / NEUTRAL)
    ├── Confidence (0.0-1.0)
    └── Metadata (reason, feature values used)
    │
    ▼
Signal Aggregator
    │
    ├── Group by symbol + direction
    ├── Weight by edge confidence
    ├── Check minimum confidence threshold
    │
    ▼
AggregatedSignal → Execution Layer
```

### Components

| Component | Role |
|-----------|------|
| **Edge Registry** | Register, validate, lifecycle management of all edges |
| **Edge Executor** | Run eligible edges per symbol within tier budget |
| **Signal Aggregator** | Combine multiple edge results into single signal per symbol |

## Edge Definition

Setiap edge adalah class dengan kontrak tetap:

```python
class Edge:
    edge_id: str                    # E001, E002, ...
    name: str
    version: int
    priority: str                   # critical | high | medium | experimental
    tier_eligibility: list[str]     # [A] | [A, B] | [A, B, C]
    required_features: list[str]    # [F002, F003, F004]
    required_context: list[str]     # [breadth_regime, sector_breadth]
    cooldown_override: int | None   # None = use tier default
```

### Edge Contract

```python
def evaluate(self, ctx: EdgeContext) -> EdgeResult:
    """
    Args:
        ctx: symbol state (features, normalization, breadth, metadata)

    Returns:
        EdgeResult with score, direction, confidence, reason
    """
```

### Edge Output (EdgeResult)

```json
{
  "edge_id": "E001",
  "edge_version": 1,
  "symbol": "TAOUSDT",
  "exchange": "BINANCE",
  "tier": "A",
  "direction": "LONG",
  "edge_score": 87,
  "confidence": 0.82,
  "reason_codes": ["OI_EXPANSION_P95", "VOLUME_EXPANSION_P88", "AI_BREADTH_88"],
  "feature_values_used": {
    "F002_OI_EXPANSION": { "raw": 3.42, "pctl_30d": 95 },
    "F003_VOLUME_EXPANSION": { "raw": 2.1, "pctl_30d": 88 },
    "F004_RS": { "raw": 1.03, "pctl_30d": 91 }
  },
  "breadth_context": {
    "sector_breadth": 88,
    "breadth_regime": "EXPANSION"
  },
  "evaluated_at": "2026-07-27T12:01:00.000Z",
  "execution_time_ms": 2.3
}
```

### Field Definitions

| Field | Description |
|-------|-------------|
| `edge_score` | 0-100. Strength of signal from this edge |
| `confidence` | 0.0-1.0. How reliable this edge considers the signal |
| `direction` | LONG, SHORT, or NEUTRAL (no signal) |
| `reason_codes` | Machine-readable codes for aggregation and debugging |
| `feature_values_used` | Snapshot of features this edge read (explainability) |
| `execution_time_ms` | How long this edge took to evaluate |

## Edge Independence

**Hard rule:** Edge tidak boleh menghitung feature sendiri. Semua feature dibaca dari store.

Edge **must** read from:
- Feature Store (raw values)
- Normalization Store (percentiles, z-scores)
- Breadth Store (sector context, regime)
- Metadata Layer (sector, listing age)

Edge **must not**:
- Compute ATR/RS/OI expansion internally
- Maintain per-symbol state (stateless)
- Call exchange APIs directly

```python
# CORRECT
oi_pctl = ctx.features.get("F002")["percentile_30d"]

# WRONG
oi_pctl = self.calculate_oi_percentile(ctx.raw_oi, ctx.historical_oi)
```

**Rationale:** Konsisten dengan ADR-004 (Feature Store is authoritative). Jika edge menghitung feature sendiri, confidence score dari FEATURE-Certification tidak berlaku.

## Edge Lifecycle

```
DISABLED ──► DRAFT ──► TESTING ──► CERTIFIED ──► DEPRECATED
                 │                     │
                 ▼                     ▼
           Not executed           Executed in production
           (logging only)         (signals sent to aggregator)
```

| Status | In Edge Engine | Signals |
|--------|----------------|---------|
| DISABLED | Not loaded | None |
| DRAFT | Loaded, not executed | Logged for analysis |
| TESTING | Executed | Logged, not sent to Aggregator |
| CERTIFIED | Executed | Sent to Aggregator |
| DEPRECATED | Loaded, not executed | Removed next release |

## Edge Priority & Tier Budget

| Priority | Examples | Tier A | Tier B | Tier C |
|----------|----------|--------|--------|--------|
| **Critical** | Liquidation cascade, Funding extreme reversal | ✅ | ✅ | ❌ |
| **High** | OI breakout, Volume momentum | ✅ | ✅ | ❌ |
| **Medium** | Compression breakout, RS trend | ✅ | ❌ | ❌ |
| **Experimental** | New edge in testing | ✅ | ❌ | ❌ |

Edge priority classification in EDGE-Registry determines which tier budget runs the edge.

## Signal Aggregator

Setelah semua eligible edge selesai mengevaluasi symbol, hasilnya digabung.

### Aggregation Rules

```python
# Per symbol, per direction
signals = [
  { "edge": "E001", "score": 87, "confidence": 0.82, "dir": "LONG" },
  { "edge": "E002", "score": 72, "confidence": 0.65, "dir": "LONG" },
  { "edge": "E003", "score": 45, "confidence": 0.30, "dir": "SHORT" },
  { "edge": "E004", "score": 0,  "confidence": 0.0,  "dir": "NEUTRAL" },
]
```

| Scenario | Rule |
|----------|------|
| **Consensus** (≥2 edges same direction, conf > 0.6) | Weighted avg score, confidence = avg |
| **Standalone** (1 edge, conf > 0.85) | Single edge signal qualifies |
| **Conflicting** (LONG and SHORT both conf > 0.6) | Reduce position size, flag for review |
| **No signal** (no edge above conf threshold) | Skip |

### Aggregated Output

```json
{
  "signal_id": "sig-20260727-120100-TAOUSDT",
  "symbol": "TAOUSDT",
  "exchange": "BINANCE",
  "direction": "LONG",
  "aggregated_score": 81,
  "aggregated_confidence": 0.74,
  "signal_type": "CONSENSUS",
  "contributing_edges": [
    { "edge_id": "E001", "score": 87, "confidence": 0.82 },
    { "edge_id": "E002", "score": 72, "confidence": 0.65 }
  ],
  "edges_evaluated": 4,
  "edges_with_signal": 2,
  "tier": "A",
  "evaluated_at": "2026-07-27T12:01:00.000Z"
}
```

### Aggregation Type

| Type | Condition | Action |
|------|-----------|--------|
| CONSENSUS | ≥2 edges, same dir, conf>0.6 | Standard signal |
| STANDALONE | 1 edge, conf>0.85 | Accept (high conviction) |
| CONFLICT | LONG + SHORT both >0.6 | Flag, reduce position |
| WEAK | All conf < 0.4 | Suppress |
| NONE | No edge triggered | Skip |

## Edge Error Isolation

Satu edge error tidak boleh mematikan edge lain.

**Rule:** Setiap edge jalan di isolated context (try/except). Error dicatat, edge lain tetap jalan.

```python
for edge in eligible_edges:
    try:
        result = edge.evaluate(ctx)
        results.append(result)
    except Exception as e:
        logger.error(f"Edge {edge.edge_id} failed: {e}")
        metrics.edge_errors[edge.edge_id] += 1
        continue  # other edges unaffected
```

## Execution Layer (Boundary)

Edge Engine menghasilkan **AggregatedSignal**. Eksekusi order (entry, exit, sizing) di luar scope ADR-010 — milik Execution Layer yang akan didefinisikan di ADR terpisah.

```
Signal Aggregator
    │
    ▼
AggregatedSignal

    │
    ▼
[EXECUTION LAYER — separate ADR]
    │
    ├── Position sizing
    ├── Order placement
    ├── Risk checks
    └── P&L tracking
```

## Edge Metrics

Per edge:

| Metric | Description |
|--------|-------------|
| `eval_count` | Total evaluations |
| `signal_count` | Number of non-NEUTRAL results |
| `avg_score` | Average edge_score when signal |
| `avg_confidence` | Average confidence when signal |
| `avg_exec_ms` | Average execution time |
| `error_count` | Total errors |
| `long_short_ratio` | Direction bias |

## Config

```yaml
# edge_engine.yaml (hot-reloadable)
aggregator:
  min_confidence_consensus: 0.6
  min_confidence_standalone: 0.85
  min_edges_for_consensus: 2
  conflict_threshold: 0.6

execution:
  max_edges_per_symbol_per_tick: 20   # cap for Tier A
  error_isolation: true                # always true

metrics:
  window_minutes: 60                   # rolling window for avg metrics
```

## Non-Goals (V1)

- Order execution (separate ADR)
- Position sizing (separate ADR)
- Risk management (separate ADR)
- ML-based signal aggregation
- Edge A/B testing per symbol
- Cross-exchange arbitrage edge

## Consequences

**Positive:**
- Edge plugin architecture: add edge = write one class + register. No pipeline changes
- Edge independence prevents feature recomputation — all read from shared stores
- Error isolation prevents single edge crash from taking down engine
- Signal Aggregator handles consensus/conflict/standalone cases explicitly
- Tier budget ensures compute cost bounded: Tier A=all, B=high, C=light
- Aggregated output with explainability (contributing edges, feature values, reason codes)
- Metrics per edge enable performance tracking and certification

**Negative:**
- Plugin architecture requires strict contract adherence — invalid contract crashes registration
- Signal Aggregator confidence thresholds arbitrary; wrong values = missed signals or false signals
- All edges must trust Feature Store freshness — edge cannot know if feature is stale without checking
- Aggregation may suppress rare but profitable standalone edges (mitigation: standalone threshold 0.85)
- Error isolation logs errors but does not auto-disable failing edge (manual)

## References

- ADR-003: Screener Architecture (Stage 8: Edge Engine)
- ADR-009: Focus Queue
- EDGE-Registry.md
- EDGE-Certification.md
