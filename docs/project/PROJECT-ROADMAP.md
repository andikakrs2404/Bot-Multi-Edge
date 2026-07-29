# PROJECT-ROADMAP

**Agent wajib baca file ini sebelum implementasi.** Menentukan fase, urutan, dan dependensi. Jangan coding di luar fase aktif tanpa persetujuan.

## Fase

| # | Fase | Dependensi | Output | Status |
|---|------|------------|--------|--------|
| 1 | Market Data Layer | — | WS adapters (Bybit, Binance), Symbol Registry, Event Bus | ⏳ |
| 2 | Feature Store | 1 | F001-F006 compute, Feature Store API, raw event store | ⬜ |
| 3 | Normalization | 2 | Percentile/rank/zscore engine, Normalization Store | ⬜ |
| 4 | Market Breadth | 2, 3 | Sector breadth, breadth regime, velocity | ⬜ |
| 5 | Attention Allocation | 3, 4 | Attention scoring, heat score, decay | ⬜ |
| 6 | Tier Assignment | 5 | Tier mgmt (A/B/C/D), hysteresis, sector guard | ⬜ |
| 7 | Focus Queue | 6 | Priority queue, round-robin, cooldown, OQ drain | ⬜ |
| 8 | Opportunity Pipeline | 1, 2 | Detector scheduler, OQ, urgency scoring, persistence | ⬜ |
| 9 | Edge Framework | 5, 7, 8 | Edge plugin system, executor, signal aggregator | ⬜ |
| 10 | Paper Trading | 9 | Simulated fills, P&L tracking, backtest framework | ⬜ |
| 11 | Execution | 10 | Live order placement, risk, position mgmt | ⬜ |

## Aturan

1. **Tidak boleh skip fase.** Setiap fase selesai (tested + documented) baru lanjut.
2. **Fase 1, 2, 3 minimal selesai sebelum tambah ADR baru.**
3. **Setiap fase punya entry criteria** (dependensi hijau) dan **exit criteria** (test passed + doc updated).
4. **Agent hanya boleh ngerjain fase aktif.** Kalau gak yakin fase aktif apa, tanya.

## Exit Criteria per Fase

### Phase 1 — Market Data Layer
- [ ] WS konek ke Bybit + Binance futures
- [ ] Reconnect otomatis dengan backoff
- [ ] Normalisasi tick ke schema seragam
- [ ] Sequence validator + timestamp enrichment
- [ ] Symbol Registry (REST, refresh 5m)
- [ ] Event Bus pub/sub untuk ticker, book, trade, liquidation
- [ ] Latency < 500ms dari exchange event → Event Bus

### Phase 2 — Feature Store
- [ ] F001-F006 compute dari raw event stream
- [ ] Feature value disimpan (raw only)
- [ ] Dependency graph di enforce
- [ ] Freshness TTL (FRESH/STALE/EXPIRED)
- [ ] Single-writer, read-only consumer pattern

### Phase 3 — Normalization
- [ ] Percentile (7/30/90d), zscore, rank engine
- [ ] Per-feature config (scope, methods, windows)
- [ ] Normalization Store (pisah dari Feature Store)
- [ ] Freshness gate — skip STALE/EXPIRED

### Phase 4 — Market Breadth
- [ ] Sector classification loaded
- [ ] Bull/bear breadth per sector
- [ ] Breadth regime (CONTRACTION/NEUTRAL/EXPANSION/EUPHORIA)
- [ ] Breadth velocity (15/30/60m)
- [ ] Leader breadth (BTC/ETH/SOL)

### Phase 5 — Attention Allocation
- [ ] Configurable weights (hot-reload)
- [ ] attention_score + heat_score + velocity
- [ ] Decay (exponential, per-cycle)
- [ ] Sector concentration guard (30%)
- [ ] Promotion/demotion hints
- [ ] Explainability (top_reasons, reason_codes)

### Phase 6 — Tier Assignment
- [ ] 4 tier (A=20, B=50, C=200, D=∞)
- [ ] Promotion/demotion hysteresis
- [ ] Capacity enforcement + displacement
- [ ] Sector guard (30% per sector)
- [ ] Sticky cycles (30/15/5)
- [ ] Refresh 60s (decouple dari attention 15s)

### Phase 7 — Focus Queue
- [ ] Priority: OQ > A > B > C > D
- [ ] Within-tier: heat_score desc
- [ ] Round-robin B/C (5/30 cycle)
- [ ] Cooldown per tier (2s/15s/60s/300s)
- [ ] Edge budget per tier
- [ ] Starvation protection (1/10 tick reserved)

### Phase 8 — Opportunity Pipeline
- [ ] Detector scheduler (SS001-SS004)
- [ ] Opportunity Engine (cooldown/expiry/urgency/enqueue)
- [ ] Persistence (OpportunityEvent store)
- [ ] Eviction (lowest urgency, CRITICAL never evicted)
- [ ] Promotion history per symbol per situation

### Phase 9 — Edge Framework
- [ ] Edge plugin system (registry + loader)
- [ ] Edge contract (evaluate → EdgeResult)
- [ ] Edge lifecycle (DISABLED → CERTIFIED → DEPRECATED)
- [ ] Error isolation (try/except per edge)
- [ ] Signal Aggregator (consensus/standalone/conflict)
- [ ] Edge metrics per edge

### Phase 10 — Paper Trading
- [ ] Simulated order matching
- [ ] P&L tracking per trade
- [ ] Backtest replay from stored events
- [ ] Performance report (win rate, PF, drawdown, expectancy)

### Phase 11 — Execution
- [ ] Live order placement
- [ ] Position sizing
- [ ] Risk checks (max loss, max position)
- [ ] P&L reconciliation
