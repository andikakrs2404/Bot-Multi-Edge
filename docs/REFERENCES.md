# References — Open Source Architecture Study

Proyek OSS yang dipelajari untuk arsitektur, bukan kode yang dipakai langsung. Setiap proyek ditentukan apa yang diambil (arsitektur/pola) dan apa yang dilewati.

## Tier S — Wajib Dipelajari

### Cryptofeed
**Ambil:** Exchange adapter architecture, feed handler, symbol normalization, reconnect logic, multi-exchange streaming
**Lewati:** Trading logic, signal logic, strategy layer
**Gunakan untuk:** ADR-002 Market Data Layer

### Hummingbot
**Ambil:** Connector architecture, event-driven design, market data abstraction, order book model, exchange isolation
**Lewati:** Strategy engine, market making, order execution layer
**Gunakan untuk:** ADR-002 Market Data Layer

## Tier A — Sangat Direkomendasikan

### Freqtrade
**Ambil:** Strategy registry, plugin system, backtest workflow, hyperparameter validation, research workflow
**Lewati:** Indicator-based strategy, bot runtime, pairlist logic
**Gunakan untuk:** ADR-010 Edge Framework, SPEC-Research-Lifecycle

### NautilusTrader
**Ambil:** Event bus, message-driven architecture, component isolation, state management, replay engine
**Lewati:** Execution layer, broker layer, OMS
**Gunakan untuk:** ADR-004 Feature Store, ADR-009 Focus Queue, ADR-010 Edge Framework

### VectorBT
**Ambil:** Factor research, feature research, signal research, vectorized evaluation
**Lewati:** Execution, live trading
**Gunakan untuk:** FEATURE-Certification, EDGE-Certification, ADR-005 Normalization

## Tier B

### Jesse
**Ambil:** Research folder structure, backtest reporting, metrics design, strategy organization
**Lewati:** Execution model, strategy runtime
**Gunakan untuk:** ADR-010 Edge Framework

### FinRL
**Ambil:** Research pipeline, experiment tracking, model registry concept
**Lewati:** RL agent, trading decisions, reward functions
**Gunakan untuk:** SPEC-Research-Lifecycle (V2)

## Tier Khusus — Future Research

### EarnHFT
**Ambil:** Router concept (pilih agent terbaik per kondisi, bukan 1 agent untuk semua)
**Lewati:** RL implementation
**Gunakan untuk:** Attention Engine + Tier Assignment routing concept (V2)

## Mapping per Dokumen

| Dokumen | Referensi Terkuat | Sifat |
|---------|-------------------|-------|
| ADR-002 Market Data | Cryptofeed + Hummingbot | Ambil arsitektur adapter |
| ADR-004 Feature Store | NautilusTrader | Event bus, state management |
| ADR-005 Normalization | VectorBT | Factor research |
| ADR-006 Breadth | Custom | Tidak ada OSS reference |
| ADR-007 Attention | Custom | IP utama — tidak ada di OSS |
| ADR-008 Tier | Custom | IP utama |
| ADR-009 Focus Queue | NautilusTrader | State management, replay |
| ADR-010 Edge Framework | Freqtrade + Jesse | Plugin system, backtest |
| ADR-011 Opportunity | Custom | IP utama |
| SPEC-Research-Lifecycle | Freqtrade + FinRL | Backtest workflow, experiment tracking |
| FEATURE-Certification | VectorBT | Factor validation |
| EDGE-Certification | VectorBT | Signal validation |

## Catatan

Bagian yang **tidak** memiliki referensi OSS kuat (Attention, Tier, Breadth, Opportunity) adalah IP utama sistem. Tidak ada proyek open-source yang mengimplementasikan pipeline:

```
Market Breadth → Attention → Tier → Focus Queue → Edge
```

sebagai sistem screener multi-edge terintegrasi.
