# EDGE-Registry

**Status:** DRAFT  
**Last Updated:** 2026-07-27  
**Owner:** Lead Architect  

---

## Registry Structure

Setiap edge wajib terdaftar di registry sebelum dieksekusi oleh Edge Engine. Registry adalah source of truth untuk semua edge.

```yaml
edge_id: E001
edge_version: 1
name: OI Breakout
family: breakout
status: CERTIFIED
priority: high
tier_eligibility: [A, B]

required_features: [F002, F003, F004]
required_context: [breadth_regime, sector_breadth]

owner: EdgeTeam
created_at: 2026-07-27
last_reviewed: 2026-09-01

hypothesis: >
  OI expansion percentile >90 combined with volume percentile >85
  and RS percentile >80 signals breakout continuation.
  Strong sector breadth confirms sector-wide participation.
```

---

## Edge Families

Edges dikelompokkan dalam family untuk dashboard, certification, dan performance attribution.

| Family | Description |
|--------|-------------|
| breakout | Volatility expansion, OI/volume spike |
| momentum | Trend following, RS, velocity |
| mean_reversion | Overextended funding, compression |
| liquidation | Liquidation cascade reversal |
| funding | Funding rate extreme reversal |
| leader_follower | Leader movement → follower lag |
| market_structure | Sweep, orderflow, imbalance |

---

## Registry Index

| ID | Name | Family | Priority | Tier | Status |
|----|------|--------|----------|------|--------|
| E001 | OI Breakout | breakout | high | A, B | CERTIFIED |
| E002 | Funding Reversal | funding | high | A, B | TESTING |
| E003 | Volume Momentum | momentum | high | A, B | CERTIFIED |
| E004 | Compression Breakout | breakout | medium | A | TESTING |
| E005 | Leader Follower | leader_follower | experimental | A | DRAFT |

---

## Edge Details

### E001 — OI Breakout

```yaml
edge_id: E001
edge_version: 1
name: OI Breakout
family: breakout
status: CERTIFIED
priority: high
tier_eligibility: [A, B]

required_features: [F002, F003, F004]
required_context: [breadth_regime, sector_breadth]

hypothesis: >
  OI expansion >P90 + volume >P85 + RS >P80 signals breakout
  continuation. Strong sector breadth confirms sector-wide
  participation, reducing false breakout risk.

owner: EdgeTeam
created_at: 2026-07-27
last_reviewed: 2026-07-27
```

**Edge logic:** Evaluate LONG when OI_PCTL > 90, VOL_PCTL > 85, RS_PCTL > 80, sector_breadth > 60. Evaluate SHORT when inverse (OI_PCTL < 10, VOL_PCTL < 15, RS_PCTL < 20, sector_breadth < 40).

**Used by:** Signal Aggregator (consensus LONG/SHORT).

---

### E002 — Funding Reversal

```yaml
edge_id: E002
edge_version: 1
name: Funding Reversal
family: funding
status: TESTING
priority: high
tier_eligibility: [A, B]

required_features: [F006]
required_context: [breadth_regime]

hypothesis: >
  Funding rate >0.05% (extreme long positioning) predicts
  SHORT reversal within 6h. Funding rate <-0.05% predicts
  LONG reversal. Reversal strength confirmed by breadth regime.

owner: EdgeTeam
created_at: 2026-07-27
last_reviewed: 2026-07-27
```

**Edge logic:** Evaluate SHORT when funding_PCTL > 90 (extreme positive), breadth_regime != CONTRACTION. Evaluate LONG when funding_PCTL < 10 (extreme negative).

**Status TESTING:** Not sent to Signal Aggregator. Logged for analysis.

---

### E003 — Volume Momentum

```yaml
edge_id: E003
edge_version: 1
name: Volume Momentum
family: momentum
status: CERTIFIED
priority: high
tier_eligibility: [A, B]

required_features: [F003, F004]
required_context: [breadth_regime]

hypothesis: >
  Volume expansion >P80 with RS >P70 confirms momentum
  continuation. Volume declining + RS declining = momentum
  exhaustion. Breadth regime filters counter-trend signals.

owner: EdgeTeam
created_at: 2026-07-27
last_reviewed: 2026-07-27
```

**Edge logic:** LONG when VOL_PCTL > 80, RS_PCTL > 70, breadth_regime != CONTRACTION. SHORT when VOL_PCTL > 80, RS_PCTL < 30, breadth_regime != EXPANSION.

---

### E004 — Compression Breakout

```yaml
edge_id: E004
edge_version: 1
name: Compression Breakout
family: breakout
status: TESTING
priority: medium
tier_eligibility: [A]

required_features: [F005, F003]
required_context: [breadth_regime]

hypothesis: >
  Low compression percentile (<20) followed by volume expansion
  (>P80) signals volatility expansion breakout. Works best in
  NEUTRAL regime (pre-breakout consolidation).

owner: EdgeTeam
created_at: 2026-07-27
last_reviewed: 2026-07-27
```

**Edge logic:** LONG when COMPRESSION_PCTL < 20, VOL_PCTL > 80, RS_PCTL rising over 3 cycles. SHORT when same conditions but RS_PCTL falling.

**Tier A only:** Too speculative for Tier B.

---

### E005 — Leader Follower

```yaml
edge_id: E005
edge_version: 1
name: Leader Follower
family: leader_follower
status: DRAFT
priority: experimental
tier_eligibility: [A]

required_features: [F004]
required_context: [sector_breadth, leader_breadth]

hypothesis: >
  When leader (BTC/ETH/SOL) moves >2% and follower in same
  sector has not moved, follower catches up within 15-30m.

owner: EdgeTeam
created_at: 2026-07-27
last_reviewed: 2026-07-27
```

**Status DRAFT:** Concept only. Not loaded in Edge Engine.

---

## Adding a New Edge

1. Add entry to registry with DRAFT status
2. Implement edge class following Edge Contract (ADR-010)
3. Set TESTING — validate output vs hypothesis
4. Run certification tests (see EDGE-Certification.md)
5. Set CERTIFIED — edge live in production signals

## Status Lifecycle

```
DRAFT ──► TESTING ──► CERTIFIED ──► DEPRECATED
              │
              ▼
         Logged only,
         not sent to
         Signal Aggregator
```

| Status | Loaded? | Executed? | Sent to Aggregator? |
|--------|---------|-----------|---------------------|
| DRAFT | No | No | No |
| TESTING | Yes | Yes | No (logged) |
| CERTIFIED | Yes | Yes | Yes |
| DEPRECATED | Yes | No | No |

---

## References

- ADR-010: Edge Framework
- EDGE-Certification.md
