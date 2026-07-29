# RESEARCH-BACKLOG

Semua ide riset. Status: IDEA → RESEARCH → TESTING → VALIDATED → REJECTED.

## Priority Order

| ID | Title | Priority | Status | Dependensi |
|----|-------|----------|--------|------------|
| RND-001 | Leader/Follower Propagation | HIGH | IDEA | Phase 4 (sector classification) |
| RND-002 | Sector Rotation Detection | HIGH | IDEA | Phase 4 (breadth) |
| RND-003 | Volume Anomaly Detection | MEDIUM | IDEA | Phase 2 (F003) |
| RND-004 | Cross-Exchange Dislocation | LOW | IDEA | Phase 1 (multi-exchange) |
| RND-005 | News Sentiment Integration | LOW | IDEA | External API |
| RND-006 | Whale Position Detection | MEDIUM | IDEA | Phase 2 (orderflow) |
| RND-007 | Spread Dislocation Edge | LOW | IDEA | Phase 1 (order book) |
| RND-008 | Liquidation Sweep Detection | MEDIUM | IDEA | Phase 1 (liquidation feed) |
| RND-009 | Adaptive Attention Weights | HIGH | IDEA | Phase 5 |
| RND-010 | Multi-Timeframe RS | MEDIUM | IDEA | Phase 3 |

## Detail

### RND-001 — Leader/Follower Propagation

```yaml
id: RND-001
title: Leader/Follower Propagation
priority: HIGH
status: IDEA
phase_dependency: Phase 4 (sector classification stabil)

description: >
  Deteksi leader movement dalam sektor, lalu cari follower yang
  belum bereaksi. Follower catch-up trade dalam 15-30m.

source_alpha: A009 (Leader Movement)
source_hypothesis: H005
blocker: Sector classification harus stabil dulu.
```

### RND-002 — Sector Rotation Detection

```yaml
id: RND-002
title: Sector Rotation Detection
priority: HIGH
status: IDEA
phase_dependency: Phase 4 (breadth engine)

description: >
  Deteksi kapital bergeser antar sektor. Breadth sector A turun,
  sector B naik. Rotasi menandakan opportunity.

source_alpha: A008 (Sector Breadth)
blocker: Breadth engine harus jalan dulu.
```

### RND-009 — Adaptive Attention Weights

```yaml
id: RND-009
title: Adaptive Attention Weights
priority: HIGH
status: IDEA
phase_dependency: Phase 5

description: >
  Bobot attention engine menyesuaikan regime pasar.
  CONTRACTION → beda bobot dari EXPANSION.

blocker: Phase 5 harus stabil dulu. V2 feature.
```

## Cara Pakai

1. Ide baru → tambah entry dengan status IDEA.
2. Kalau ada blocker → isi `blocker`.
3. Begini dikerjakan → status jadi RESEARCH.
4. Propose fase berapa ide ini dikerjakan.
