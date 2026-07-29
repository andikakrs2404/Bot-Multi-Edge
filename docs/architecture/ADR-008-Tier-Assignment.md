# ADR-008: Tier Assignment

**Status:** DRAFT  
**Date:** 2026-07-27  
**Author:** Lead Architect  
**Deciders:** Lead Architect  

---

## Context

Attention Engine (ADR-007) menghasilkan attention_score dan heat_score per symbol. Tapi score saja tidak cukup — sistem perlu memetakan score ke **tier diskrit** dengan kapasitas, hysteresis, dan prioritas.

Tier Assignment adalah jembatan antara Attention Engine dan Focus Queue. Tidak menghitung score baru — hanya memetakan.

```
Attention Store (scores, hints)
    │
    ▼
Tier Assignment
    │
    ├──► Tier A (top capacity)
    ├──► Tier B (secondary)
    ├──► Tier C (tertiary)
    └──► Tier D (universe)
           │
           ▼
Focus Queue (ADR-009)
```

## Decision

Build **Tier Assignment Engine** dengan 5 aturan: Promotion Priority, Hysteresis, Capacity Enforcement, Sector Guard, Sticky Duration. Tidak ada logic scoring — murni mapping.

## Tier Definitions

```yaml
tiers:
  A:
    label: "Hot"
    capacity: 20
    promotion_threshold_heat: 80
    demotion_threshold_attention: 65
    evaluation_frequency: "every_tick"
    sticky_cycles: 30

  B:
    label: "Watch"
    capacity: 50
    promotion_threshold_heat: 60
    demotion_threshold_attention: 40
    evaluation_frequency: "every_5_ticks"
    sticky_cycles: 15

  C:
    label: "Scan"
    capacity: 200
    promotion_threshold_heat: 30
    demotion_threshold_attention: 25
    evaluation_frequency: "every_30_ticks"
    sticky_cycles: 5

  D:
    label: "Universe"
    capacity: unlimited
    evaluation_frequency: "on_demand"
    sticky_cycles: 0
```

### Capacity rationale

| Tier | Capacity | Basis |
|------|----------|-------|
| A | 20 | Top ~2% of 1000 universe. Edge Engine can process 20/tick |
| B | 50 | Next ~5%. Evaluated less frequently |
| C | 200 | Remaining candidates from Stage 1. Periodic scan |
| D | ∞ | Full universe. Visible but not actively evaluated |

## Promotion / Demotion Hysteresis

Hysteresis mencegah flapping — symbol naik turun tier setiap siklus.

Threshold promosi berbeda dari threshold demosi:

| Tier | Promotion (need heat ≥) | Demotion (need attention ≤) | Gap |
|------|------------------------|----------------------------|-----|
| A | 80 (heat) | 65 (attention) | 15 |
| B | 60 (heat) | 40 (attention) | 20 |
| C | 30 (heat) | 25 (attention) | 5 |

### Promotion Rules

Promoted when **all** conditions met:

1. `heat_score >= threshold` (fast reaction)
2. Not currently in sticky period (if just promoted)
3. Tier has available capacity (or displaces lowest)

### Demotion Rules

Demoted when **any** condition met:

1. `attention_score <= demotion_threshold` for 3 consecutive cycles (confirmed decay)
1. `data_freshness == EXPIRED` for feature set (WS disconnected)
2. `symbol_removed` event received (delisted)

### Why hysteresis matters

Without gap:

```
Cycle 1: score=80 → Tier A
Cycle 2: score=79 → Tier B
Cycle 3: score=81 → Tier A
```

With hysteresis (promote at 80, demote at 65):

```
Cycle 1:  score=80 → Tier A
Cycle 2:  score=79 → still Tier A (above 65)
Cycle 10: score=60 → Tier B (confirmed decay)
```

## Capacity Enforcement

Setiap tier punya slot maksimum. Jika eligible symbol melebihi kapasitas, lowest-score symbol turun ke tier bawah.

### Selection order per tier

```
1. Sticky symbols (already in tier, sticky active)
2. Opportunity Queue symbols (special_bonus=50)
3. Heat score descending (best remaining)
4. Attention score descending (tiebreaker)
```

### Overflow

| Scenario | Action |
|----------|--------|
| Tier A has 27 eligible, capacity 20 | Top 20 by heat_score stay. Bottom 7 → Tier B |
| Tier B has 70 eligible, capacity 50 | Top 50 by heat_score stay. Bottom 20 → Tier C |
| Tier C has 300 eligible, capacity 200 | Top 200 stay. Rest → Tier D |
| Tier D overflows | No cap. Periodic scan still runs |

### Displacement

Ketika symbol baru harus masuk tier penuh, **symbol non-sticky dengan heat terendah** di tier itu turun satu tingkat.

Displaced symbol tidak dihukum — score dipertahankan, bisa kompetisi siklus berikutnya.

## Promotion Priority

Urutan siapa naik ke tier lebih tinggi:

```
1. Opportunity Queue symbols (special_bonus=50 — bypass heat check)
2. By heat_score descending (highest urgency)
3. By attention_score descending (tiebreaker)
4. Sticky symbols demoted from higher tier (first bid for current tier)
```

Special situation selalu menang.

## Refresh Frequency

| Engine | Frequency | Rationale |
|--------|-----------|-----------|
| Attention score update | Every Normalization cycle (~15s) | Fast reaction to market changes |
| Tier Assignment | Every **60s** | Prevents flapping. Score changes need confirmation |
| Focus Queue update | Every Tier Assignment cycle | Queue reflects current tier state |

Tier refresh every 60s regardless of attention update frequency. Prevents micro-flapping.

## Sector Guard Integration

Sector Concentration Guard dari ADR-007 diterapkan di Tier Assignment.

**Rule:** Max 30% of Tier A+B slots from one sector.

```
Tier A+B total capacity = 70
Max per sector = 21
```

Jika sektor melebihi, symbol dengan heat terendah di sektor itu ditahan di Tier C.

Guard diterapkan **setelah** Promotion Priority — Opportunity Queue dan high-heat symbol tetap masuk, hanya yang borderline terbatas.

## Tier Assignment Output

```json
{
  "tier_snapshot_id": "tier-20260727-120100",
  "tiers": {
    "A": {
      "symbols": [
        { "symbol": "BTCUSDT", "heat_score": 92, "attention_score": 88, "sticky_remaining": 25 },
        { "symbol": "TAOUSDT", "heat_score": 88, "attention_score": 85, "sticky_remaining": 12 }
      ],
      "count": 20,
      "capacity": 20
    },
    "B": {
      "symbols": [
        { "symbol": "ETHUSDT", "heat_score": 72, "attention_score": 70, "sticky_remaining": 10 }
      ],
      "count": 50,
      "capacity": 50
    },
    "C": {
      "symbols": [],
      "count": 150,
      "capacity": 200
    },
    "D": {
      "symbols": [],
      "count": 580,
      "capacity": null
    }
  },
  "promotions": [
    { "symbol": "RNDRUSDT", "from": "B", "to": "A", "reason": "heat_score 85, sector AI" }
  ],
  "demotions": [
    { "symbol": "DOGEUSDT", "from": "A", "to": "B", "reason": "attention_score 60, 3 cycles below threshold" }
  ],
  "sector_guard_applied": ["AI"],
  "assigned_at": "2026-07-27T12:01:00.000Z"
}
```

## Consumer Map

| Consumer | Reads | What |
|----------|-------|------|
| Stage 7: Focus Queue (ADR-009) | Tier assignments per symbol | Build ordered queue |
| Stage 8: Edge Engine | Symbol tier membership | Filter evaluation frequency |
| Dashboard UI | Tier snapshot | Human monitoring |

## Config

```yaml
# tier_config.yaml (hot-reloadable)
tier_a:
  capacity: 20
  promotion_heat: 80
  demotion_attention: 65
  sticky_cycles: 30

tier_b:
  capacity: 50
  promotion_heat: 60
  demotion_attention: 40
  sticky_cycles: 15

tier_c:
  capacity: 200
  promotion_heat: 30
  demotion_attention: 25
  sticky_cycles: 5

tier_d:
  capacity: null

sector_guard:
  max_share_pct: 30
  enabled: true

refresh_interval_seconds: 60
```

## Non-Goals (V1)

- Score computation (belongs to ADR-007)
- Queue ordering (belongs to ADR-009)
- Adaptive capacity (capacity stays static in V1)
- ML-based tier prediction

## Consequences

**Positive:**
- Hysteresis prevents flapping — Tier A symbol stays A even with small score dip
- Capacity enforcement guarantees Edge Engine bounded compute cost
- Promotion Priority ensures Special Situation always wins
- Sector Guard prevents sector monoculture in Focus Queue
- Tier refresh at 60s decouples from attention 15s — stable tiers
- Displaced symbols not penalized — fair competition next cycle

**Negative:**
- 60s refresh adds latency — symbol must wait up to 60s for tier change
- Sector Guard may block cross-sector momentum (AI spills to INFRA, but guard limits AI)
- Capacity static — in high-volatility regime, 20 Tier A slots may be too few
- Sticky duration adds inertia — decaying symbol wastes Tier A slot for 30 cycles

## References

- ADR-003: Screener Architecture (Stage 6: Tier Assignment)
- ADR-007: Attention Allocation
- ADR-009: Focus Queue
