# GITHUB-REFERENCE-ARCHITECTURE

Proyek OSS yang dipelajari arsitekturnya. Bukan kode yang dipakai langsung. Setiap baris adalah keputusan sadar: apa yang diambil, apa yang dilewati, dan kenapa.

## cryptofeed

```yaml
ambil:
  - websocket architecture: multi-exchange adapter pattern
  - feed handler: normalized tick per exchange
  - symbol normalization: standardisasi nama symbol
  - reconnect logic: exponential backoff + jitter
  - multi-exchange streaming: satu proses handle N exchange

lewatkan:
  - trading logic: sistem punya pipeline sendiri
  - signal logic: gak relevan untuk screener
  - strategy layer: Edge Engine urusan kita

dipakai_di: ADR-002 Market Data Layer
```

## hummingbot

```yaml
ambil:
  - connector architecture: per-exchange connector pattern
  - event-driven design: pub/sub antar komponen
  - market data abstraction: satu interface untuk semua exchange
  - order book model: local order book reconstruction
  - exchange isolation: satu exchange mati, lain jalan

lewatkan:
  - strategy engine: bot-specific
  - market making logic: gak relevan
  - order execution layer: Phase 11 urusan kita

dipakai_di: ADR-002 Market Data Layer
```

## nautilus_trader

```yaml
ambil:
  - event bus: message-driven antar komponen
  - state management: component isolation + state machine
  - replay engine: event sourcing untuk backtest
  - component isolation: tiap komponen independen

lewatkan:
  - execution layer: broker-specific
  - OMS: order management system
  - position sizing: Phase 11

dipakai_di: ADR-004 Feature Store, ADR-009 Focus Queue, ADR-010 Edge Framework
```

## freqtrade

```yaml
ambil:
  - strategy registry: plugin system untuk edge
  - backtest workflow: walk-forward, hyperopt concept
  - hyperparameter validation: optimasi threshold
  - research workflow: experiment → validate → deploy

lewatkan:
  - indicator-based strategy: kita pake feature pipeline
  - bot runtime: long-running bot berbeda
  - pairlist logic: kita punya Attention Engine

dipakai_di: ADR-010 Edge Framework, SPEC-Research-Lifecycle
```

## vectorbt

```yaml
ambil:
  - factor research: vectorized feature validation
  - signal research: signal quality testing
  - vectorized evaluation: jutaan simulasi cepat

lewatkan:
  - execution: paper only
  - live trading: gak relevan

dipakai_di: FEATURE-Certification, EDGE-Certification, ADR-005 Normalization
```

## jesse

```yaml
ambil:
  - research folder structure: organisasi riset
  - backtest reporting: metrics layout
  - metrics design: win rate, PF, drawdown, expectancy
  - strategy organization: per-strategy folder

lewatkan:
  - execution model: beda pendekatan
  - strategy runtime: kita punya Edge Engine

dipakai_di: ADR-010 Edge Framework
```

## finrl

```yaml
ambil:
  - experiment tracking: log tiap experiment
  - model registry concept: versi untuk setiap model

lewatkan:
  - RL agent: terlalu dini
  - reward functions: butuh environment stabil dulu

dipakai_di: SPEC-Research-Lifecycle (V2)
```

## graphify (Graphify-Labs/graphify)

```yaml
ambil:
  - knowledge graph concept: feature → edge → hypothesis → situation relationships
  - query/path tracing: navigate dependency graph
  - god nodes + surprising connections: detect hidden coupling
  - token-efficient query: 71x reduction vs raw files

lewatkan:
  - AST extraction: kita bukan library code
  - image vision extraction: gak relevan
  - file watching: pipeline kita event-driven

dipakai_di: R&D dashboard / research artifact graph (Phase 9+)

dampak:
  - Grafik feature → edge → situation dalam satu view
  - Lacak dependensi tak terduga antar komponen
  - Query cepat tanpa baca file mentah
```

## ponytail (DietrichGebert/ponytail)

```yaml
ambil:
  - AGENTS.md philosophy: reuse before build, simplify before create
  - decision ladder: agent must prove existing can't solve problem
  - architecture discipline: governance layer for agent output
  - ponytail rules: before_new_feature, before_new_edge, before_new_detector

lewatkan:
  - runtime architecture: sistem kita beda
  - plugin implementation: tidak relevan
  - coding style restrictions: terlalu preskriptif

dipakai_di: AGENT.md (Ponytail Rules section), seluruh fase

dampak:
  - prevents feature explosion (F001-F087 dalam 6 bulan)
  - prevents edge explosion (E001-E041 overlap)
  - reduces technical debt
  - improves agent output quality
  - forces proof before creation
```

## earnhft

```yaml
ambil:
  - router concept: pilih agent terbaik per kondisi pasar
  - bukan 1 agent untuk semua: mirror Attention → Tier routing

lewatkan:
  - RL implementation: terlalu kompleks untuk V1

dipakai_di: Attention Engine routing concept (V2)
```

## 21st MCP (21st-dev/magic-mcp)

```yaml
ambil:
  - MCP-based UI generation: prompt → React component (Tailwind + shadcn)
  - component search: 10K+ library dari 21st.dev
  - UI generation from data domain (tables, dashboards, cards, heatmaps)

lewatkan:
  - AI image generation: bukan ini
  - full app scaffolding: overkill untuk komponen spesifik

dipakai_di: Dashboard UI (Phase 9+) — Attention Heatmap, Opportunity Queue table, Tier Overview, Screener Metrics

dampak:
  - Dashboard screener crypto futures dari prompt
  - attention_score, heat_score, opportunity_queue, sector_breadth → langsung jadi komponen
  - UI konsisten pakai shadcn + Tailwind tanpa manual styling
```

## Summary

### UI / Dashboard Stack

| Layer | Primary Reference | Sifat |
|-------|------------------|-------|
| Design System | shadcn/ui + Tailwind + Lucide Icons | Foundation UI |
| Charts | Recharts (line/area/bar), ECharts (treemap/heatmap) | Visualisasi |
| Dashboard Reference | Fincept Terminal (layout, multi-panel, dock), OpenBB (widget, workspace) | Inspirasi layout |
| UI Generation | 21st MCP (prompt → React component) | Akselerasi UI |
| Example App | shadcn/taxonomy (Next.js + shadcn + Tailwind) | Pola layout reference |
| UX Guardian | ui-agent.md, ux-agent.md, dashboard-agent.md | Konsistensi UI/UX |

### Backend Architecture

| Layer | Primary Reference | Sifat |
|-------|------------------|-------|
| Market Data | cryptofeed + hummingbot | Ambil adapter pattern |
| State Management | nautilus_trader | Event bus, replay |
| Feature Research | vectorbt | Factor validation |
| Edge Framework | freqtrade + jesse | Plugin system, backtest |
| Knowledge Graph | graphify | R&D artifact relationship |
| Agent Governance | ponytail | Reuse before build, simplify before create |
| Attention / Tier / Breadth / Opportunity | **Custom** | **IP utama — tidak ada OSS reference** |

## UI Detail References

### shadcn/ui (shadcn-ui/ui)

```yaml
ambil:
  - component library: Table, Dialog, Drawer, Command Palette, Toast, Form
  - copy-paste model: komponen diambil dan dimodifikasi langsung di proyek
  - dark mode first: sesuai trading terminal
  - aksesibilitas built-in

lewatkan:
  - full design system dengan CSS vars terpisah (kami extend)

dipakai_di: Semua UI Phase 9+
```

See also: taxonomy (shadcn-ui/taxonomy) — contoh Next.js + shadcn app dengan sidebar, settings, table patterns.

### Tremor (tremorlabs/tremor)

```yaml
ambil:
  - analytics dashboard components: Area Chart, Line Chart, Donut, Bar, Heatmap
  - KPI dashboard layout
  - monitoring widget

lewatkan:
  - full framework (shadcn lebih fleksibel)
  - specific data provider patterns

dipakai_di: Dashboard metrics (Phase 9+)
```

### Fincept Terminal (fincept-corporation/fincept-terminal)

```yaml
ambil:
  - layout terminal: multi-panel, dock system, sidebar
  - workspace concept
  - terminal aesthetic untuk trading

lewatkan:
  - data sources (kami punya pipeline sendiri)
  - execution logic

dipakai_di: Dashboard layout reference (Phase 9+)
```

### OpenBB (OpenBB-finance/OpenBB)

```yaml
ambil:
  - research workflow
  - widget system
  - data panels
  - workspace concept

lewatkan:
  - data providers
  - broker integration

dipakai_di: Dashboard layout reference + widget system (Phase 9+)
```

### Recharts (recharts/recharts)

```yaml
ambil:
  - Line chart: Heat Score trend, Attention trend
  - Area chart: Breadth history
  - Bar chart: Signal rate per edge
  - Responsive container

lewatkan:
  - treemap (ECharts lebih kuat)

dipakai_di: Dashboard charts (Phase 9+)
```

### Apache ECharts (apache/echarts)

```yaml
ambil:
  - Treemap: Sector allocation, Market map
  - Heatmap: Attention matrix (symbol × feature)
  - Graph: Dependensi antar komponen
  - Kaya akan chart types

lewatkan:
  - React wrapper (pakai echarts-for-react)

dipakai_di: Advanced visualisasi (Phase 9+)
```

## UI/UX Agent Rules

### ui-agent.md

```yaml
role: Design System Guardian
rules:
  - Komponen WAJIB dari shadcn jika ada. Jangan buat custom.
  - Styling WAJIB Tailwind utility classes. Jangan CSS terpisah.
  - Dark mode first. Light mode opsional, jangan prioritaskan.
  - Ikon WAJIB dari Lucide Icons.
  - Jangan tambah dependency UI baru kalau shadcn sudah punya.
```

### ux-agent.md

```yaml
role: Trading UX Guardian
rules:
  - Setiap informasi harus menjawab: APA? KENAPA? TINDAKAN?
  - Contoh buruk: "Heat Score = 87"
  - Contoh baik: "Heat Score = 87 — OI P96, Vol P91, AI Breadth Rising → MASUK OPPORTUNITY QUEUE"
  - Hindari angka mentah tanpa konteks.
  - Setiap signal harus punya reason codes.
```

### dashboard-agent.md

```yaml
role: Dashboard Consistency Guardian
panels:
  - Scanner
  - Focus Queue
  - Opportunity Queue
  - Signals
  - Trades
  - Metrics

rules:
  - Semua panel pakai layout yang sama (header, content, footer pattern)
  - Konsisten dalam: font size, spacing, color palette, border radius
  - Setiap panel bisa di-minimize/dock/close
  - Layout tersimpan per workspace
```

## Agent Stack Priority

| Prioritas | Tool | Fungsi | Fase |
|-----------|------|--------|------|
| ⭐⭐⭐⭐⭐ | Graphiti (getzep/graphiti) | Temporal Knowledge Graph — relasi ADR→hypothesis→feature→edge→signal | Phase 0 (sekarang) |
| ⭐⭐⭐⭐⭐ | OpenTelemetry + Langfuse | Observability — trace agent + pipeline latency per stage | Phase 1+ |
| ⭐⭐⭐⭐ | Ponytail | Governance — reuse before build, simplify | Phase 0 ✅ |
| ⭐⭐⭐⭐ | Graphify | Codebase knowledge graph — navigasi file cepat | Phase 0 ✅ |
| ⭐⭐⭐⭐ | GitHub MCP | Repository intelligence — baca issue/PR, buat branch/PR | Phase 0 |
| ⭐⭐⭐ | Mem0 | Long-term memory | V2 |
| ⭐⭐⭐ | 21st MCP | UI generation | Phase 9+ |

## graphiti (getzep/graphiti)

```yaml
ambil:
  - temporal knowledge graph: entity + relationship + time dimension
  - MCP server built-in: integrasi langsung dengan agent
  - tracking: ADR → Hypothesis → Feature → Edge → Signal → Trade
  - query temporal: "Kenapa E017 dibuat? Feature apa? Hypothesis mana?"

lewatkan:
  - full UI (pake API/MCP aja)
  - real-time ingestion (kita update periodik)

dipakai_di: Semua fase — knowledge backbone untuk agent

dampak:
  - Agent tahu histori keputusan arsitektur
  - Agent tahu relasi feature → edge → hypothesis
  - Tidak ada duplicate feature/edge karena agent bisa query dulu
  - Proyek masih rapi setelah 12+ bulan
```

## langfuse + opentelemetry

```yaml
ambil:
  - tracing coding agents: prompt → tool call → file changed → error
  - cost tracking per agent session
  - pipeline latency tracing: WS Receive → Feature → Attention → Edge
  - agent evaluation: mana agent yang hasilnya buruk?

lewatkan:
  - self-hosting (pakai cloud dulu, self-host kalau perlu)

dipakai_di: Phase 1+ — observability agent + pipeline latency

dampak:
  - Latency per stage: Feature 3ms, Attention 2ms, Edge 48ms — tahu mana bottleneck
  - Agent buruk ketahuan: prompt apa, tool call apa, error apa
  - Optimasi berdasarkan data, bukan tebakan
```

## github mcp

```yaml
ambil:
  - baca issue, ADR, PR, review langsung dari agent context
  - buat branch, buat PR, commit dari agent
  - repository intelligence

lewatkan:
  - self-hosted GitHub

dipakai_di: Semua fase — development workflow

dampak:
  - Agent bisa review PR existing sebelum buat perubahan duplikat
  - Agent bisa buat PR langsung
  - Issue tracking terintegrasi
```

## Internal Agent Definitions

### architecture-agent.md

```yaml
role: Architecture Guardian
tugas:
  - Review ADR baru konsisten dengan ADR existing
  - Cek dependency antar komponen
  - Cek ownership (siapa owner komponen ini?)
  - Reject ADR yang overlap atau ga perlu
trigger: Sebelum ADR baru disetujui
```

### registry-guardian-agent.md

```yaml
role: Registry Guardian
tugas:
  - Sebelum Feature baru: cek FEATURE-Registry — existing? extension? overlap?
  - Sebelum Edge baru: cek EDGE-Registry — existing? modification? overlap?
  - Sebelum Detector baru: cek SPEC-Special-Situations
  - Implementasi filosofi Ponytail
trigger: Sebelum entry registry baru dibuat
```

### research-agent.md

```yaml
role: Research Agent
tugas:
  - GitHub scan: cari paper/repo baru relevan
  - Update RESEARCH-BACKLOG dengan temuan baru
  - Generate hypothesis dari market observation
  - Validasi hypothesis existing dengan data baru
trigger: Periodik (harian/mingguan)
```

### performance-agent.md

```yaml
role: Performance Agent
tugas:
  - Profiling pipeline latency per stage
  - CPU/memory analysis per komponen
  - Deteksi bottleneck (edge terlalu lambat? queue penuh?)
  - Rekomendasi optimasi
trigger: Periodik + saat latency spike
```
