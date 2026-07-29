# SYSTEM-CONSTRAINTS

Constraint operasional per target hardware. Semua keputusan arsitektur (kapasitas, budget, threshold) harus konsisten dengan file ini.

## Desktop

```
CPU:  i3 Gen13
GPU:  GTX 1660 Ti
RAM:  ~16 GB (estimasi)
OS:   Windows 10
```

```yaml
profile: desktop
universe_max: 1000
tiers:
  A_max: 20
  B_max: 50
  C_max: 200
  D: unlimited

latency_sla_ms:
  total_signal_path: 1000
  market_data: 500
  feature_store: 100
  normalization: 50
  breadth: 50
  attention: 50
  tier: 50
  edge_per_symbol: 50

memory_estimate_mb:
  symbol_state_per_1000: 500
  order_book_per_exchange: 200
  total_peak: ~1200

edge_budget: full
feature_cache: all
breadth_enabled: true
```

## Jetson Nano 2GB

```
CPU:  Quad-core ARM Cortex-A57
GPU:  128-core Maxwell
RAM:  2 GB shared
OS:   Linux (Ubuntu/JetPack)
```

```yaml
profile: jetson_nano_2gb
universe_max: 300
tiers:
  A_max: 15
  B_max: 25
  C_max: 100
  D: unlimited

latency_sla_ms:
  total_signal_path: 2000
  market_data: 1000
  feature_store: 200
  normalization: 100
  breadth: 100
  attention: 100
  tier: 100
  edge_per_symbol: 100

memory_estimate_mb:
  symbol_state_per_300: 150
  order_book_per_exchange: 100
  total_peak: ~700
  hard_limit: 1500

edge_budget: lightweight_only
feature_cache: partial
breadth_enabled: true
```

## Low VPS (2 vCPU, 4GB RAM)

```yaml
profile: vps_low
universe_max: 500
tiers:
  A_max: 10
  B_max: 20
  C_max: 100
  D: unlimited

latency_sla_ms:
  total_signal_path: 2000
  market_data: 1000
  feature_store: 200
  normalization: 100
  breadth: null
  attention: 100
  tier: 100
  edge_per_symbol: 100

memory_estimate_mb: ~800
edge_budget: high_priority_only
feature_cache: tier_ab_only
breadth_enabled: false
```

## Hard Limits (semua profile)

```yaml
hard_limits:
  ram_mb: 1500           # Safety limit. System degrades before hitting this.
  edge_timeout_ms: 50     # Per edge evaluation. Kill if exceeded.
  queue_max_wait_ms: 5000 # Max wait in queue before eviction.
  ws_reconnect_max_attempts: 10
  ws_reconnect_backoff_max_s: 60
```

## Cara Pakai

1. Semua implementasi harus bisa jalan di desktop profile (target utama).
2. Jetson profile = constraint untuk lightweight mode.
3. Kalau ada trade-off arsitektur, refer ke sini.
