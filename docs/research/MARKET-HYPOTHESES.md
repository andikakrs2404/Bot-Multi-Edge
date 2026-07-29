# MARKET-HYPOTHESES

Kitab suci penelitian. Semua feature dan edge berasal dari hipotesis di sini. Status: IDEA → RESEARCH → TESTING → VALIDATED → REJECTED.

## Aktif

### H001 — OI Expansion precedes breakout

```yaml
id: H001
title: OI Expansion precedes breakout
status: VALIDATED
confidence: 93

hypothesis: >
  OI expansion > P90 combined with volume expansion > P85
  predicts above-average 1h forward returns.

source_features: [F002, F003]
source_edges: [E001, E004]

validated_by: FEATURE-Certification (E001)
validated_at: 2026-07-27
```

### H002 — Volume momentum continuation

```yaml
id: H002
title: Volume momentum continuation
status: VALIDATED
confidence: 88

hypothesis: >
  Volume expansion > P80 with RS > P70 confirms momentum continuation.
  Volume declining + RS declining = momentum exhaustion.

source_features: [F003, F004]
source_edges: [E003]

validated_by: FEATURE-Certification (E003)
validated_at: 2026-07-27
```

### H003 — Funding extreme mean reversion

```yaml
id: H003
title: Funding extreme mean reversion
status: TESTING
confidence: 72

hypothesis: >
  Funding rate > 0.05% predicts SHORT reversal within 6h.
  Funding rate < -0.05% predicts LONG reversal.

source_features: [F006]
source_edges: [E002]

validated_by: EDGE-Certification (E002 — TESTING)
validated_at: 2026-07-27
notes: Sample masih kecil (4.5K). Butuh data 3x lipat.
```

### H004 — Compression breakout

```yaml
id: H004
title: Compression precedes volatility expansion
status: TESTING
confidence: 55

hypothesis: >
  Low compression percentile (<20) followed by volume expansion (>P80)
  signals volatility expansion breakout.

source_features: [F005, F003]
source_edges: [E004]

validated_by: EDGE-Certification (E004 — TESTING)
validated_at: 2026-07-27
notes: Sample terlalu kecil (1.8K). Win rate masih 49.5%.
```

### H005 — Leader moves first, follower catches up

```yaml
id: H005
title: Leader moves first, follower catches up
status: IDEA
confidence: null

hypothesis: >
  When leader (BTC/ETH/SOL) moves > 2% and follower in same sector
  has not moved proportionally, follower catches up within 15-30m.

source_features: [F004]
source_edges: [E005]

validated_by: null
notes: V2. Butuh sector classification stabil dulu.
```

## Riwayat

### H006 — Compression P90 (REJECTED)

```yaml
id: H006
title: Compression P90 predicts reversal
status: REJECTED
rejected_at: 2026-07-27
alasan: >
  Sample terlalu kecil (< 500). Tidak ada improvement signifikan
  terhadap baseline.
```

## Template Hipotesis Baru

```yaml
id: HXXX
title: <judul>
status: IDEA
confidence: null

hypothesis: >
  <pernyataan hipotesis>

source_features: []
source_edges: []
validated_by: null
notes: <ide awal>
```
