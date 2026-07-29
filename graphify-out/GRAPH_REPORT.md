# Graph Report - future-trading-bot-rnd  (2026-07-29)

## Corpus Check
- 89 files · ~45,477 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1116 nodes · 1730 edges · 74 communities (61 shown, 13 thin omitted)
- Extraction: 86% EXTRACTED · 14% INFERRED · 0% AMBIGUOUS · INFERRED: 236 edges (avg confidence: 0.54)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `4adef369`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- MarketEvent
- ObservabilityStore
- devDependencies
- GITHUB-REFERENCE-ARCHITECTURE
- ADR-012: Observability Platform
- ADR-007: Attention Allocation Engine
- ADR-011: Opportunity Pipeline
- Exchange
- compilerOptions
- ADR-006: Market Breadth
- ADR-009: Focus Queue
- ADR-003
- ADR-003: Screener Architecture
- ConnectionStatus
- ADR-010: Edge Engine Framework
- ADR-005: Feature Normalization
- ADR-008: Tier Assignment
- EventBus
- SPEC-Research-Lifecycle
- SPEC-Special-Situations
- SPEC-Screener
- SPEC-Sector-Classification
- Sub-Objects
- api.ts
- ADR-002: Market Data Layer
- Event
- __init__.py
- ADR-004: Feature Store
- Exit Criteria per Fase
- References — Open Source Architecture Study
- EDGE-Certification
- Certifications
- FEATURE-Registry
- EDGE-Registry
- binance.py
- AGENT GUIDELINES
- EventType
- TestSequenceValidator
- ADR-001: System Overview
- Aktif
- SPEC-Signal-Attribution
- Timestamps
- page.tsx
- ALPHA-SOURCES
- Detail
- layout.tsx
- SYSTEM-CONSTRAINTS
- TECH-DEBT
- DECISION-LOG
- page.tsx
- AGENTS.md
- next.config.js
- next-env.d.ts
- README.md
- __init__.py
- AGENT
- DECISION-LOG
- PROJECT-Roadmap
- REFERENCES
- SYSTEM-Constraints
- TECH-DEBT
- future-trading-bot-rnd
- PerSymbolOrderedBus
- api.py
- Event

## God Nodes (most connected - your core abstractions)
1. `MarketEvent` - 64 edges
2. `Exchange` - 56 edges
3. `EventBus` - 46 edges
4. `FeatureId` - 44 edges
5. `SymbolFeatureState` - 33 edges
6. `FeatureStore` - 32 edges
7. `NormalizationEngine` - 28 edges
8. `SymbolWindowState` - 28 edges
9. `EventType` - 28 edges
10. `RawFeature` - 26 edges

## Surprising Connections (you probably didn't know these)
- `BreadthEngine` --uses--> `EventBus`  [INFERRED]
  features/breadth.py → market_data/event_bus.py
- `FeatureHandler` --uses--> `EventBus`  [INFERRED]
  features/feature_store.py → market_data/event_bus.py
- `FeatureHandler` --uses--> `EventType`  [INFERRED]
  features/feature_store.py → market_data/events.py
- `FeatureHandler` --uses--> `Exchange`  [INFERRED]
  features/feature_store.py → market_data/events.py
- `FeatureStore` --uses--> `EventBus`  [INFERRED]
  features/feature_store.py → market_data/event_bus.py

## Import Cycles
- None detected.

## Communities (74 total, 13 thin omitted)

### Community 0 - "MarketEvent"
Cohesion: 0.07
Nodes (45): FeatureHandler, Protocol, FeatureStore — authoritative state owner per ADR-004.  Ingest → route → handler, CandleHandler, _feature(), FeatureHandler, FundingHandler, LiquidationHandler (+37 more)

### Community 1 - "ObservabilityStore"
Cohesion: 0.06
Nodes (29): BaseModel, deque, FastAPI, Observability API — FastAPI app with CORS.  Wires up pipeline EventBus, SymbolRe, ExchangeStatus, Pydantic response models for observability API., SymbolListResponse, SymbolResponse (+21 more)

### Community 2 - "devDependencies"
Cohesion: 0.05
Nodes (36): autoprefixer, dependencies, lucide-react, next, react, react-dom, recharts, @tanstack/react-table (+28 more)

### Community 3 - "GITHUB-REFERENCE-ARCHITECTURE"
Cohesion: 0.06
Nodes (35): 21st MCP (21st-dev/magic-mcp), Agent Stack Priority, Apache ECharts (apache/echarts), architecture-agent.md, Backend Architecture, cryptofeed, dashboard-agent.md, earnhft (+27 more)

### Community 4 - "ADR-012: Observability Platform"
Cohesion: 0.06
Nodes (30): ADR-012: Observability Platform, Alerting (placeholder), API Contract V1, Architecture, Consequences, Context, Core Principle: Producer Owns Metrics, Dashboard V1 Pages (+22 more)

### Community 5 - "ADR-007: Attention Allocation Engine"
Cohesion: 0.07
Nodes (29): ADR-007: Attention Allocation Engine, Architecture, Attention Decay, Attention Explainability, Attention Formula, Attention Record (per symbol), Attention Store, Attention Velocity (+21 more)

### Community 6 - "ADR-011: Opportunity Pipeline"
Cohesion: 0.07
Nodes (27): ADR-011: Opportunity Pipeline, Architecture, Components, Config, Consequences, Context, Cooldown Tracker, Decision (+19 more)

### Community 7 - "Exchange"
Cohesion: 0.21
Nodes (8): Exchange, _infer_sector(), Strip quote suffix + numeric prefix, then match keywords., Auto-discovers symbols from exchange REST APIs.      - Polls every interval_sec, SymbolMeta, SymbolRegistry, _lifespan(), str

### Community 8 - "compilerOptions"
Cohesion: 0.07
Nodes (26): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+18 more)

### Community 9 - "ADR-006: Market Breadth"
Cohesion: 0.08
Nodes (25): ADR-006: Market Breadth, Architecture, Breadth Quality, Breadth Regimes, Breadth Snapshot, Breadth Store, Breadth Velocity, Bull vs Bear Breadth (+17 more)

### Community 10 - "ADR-009: Focus Queue"
Cohesion: 0.08
Nodes (25): ADR-009: Focus Queue, Config, Consequences, Consumer Map, Context, Decision, Dequeue (pop), Drain Policy (+17 more)

### Community 11 - "ADR-003"
Cohesion: 0.13
Nodes (25): ADR-001, ADR-002, ADR-003, ADR-004, ADR-005, ADR-006, ADR-007, ADR-008 (+17 more)

### Community 12 - "ADR-003: Screener Architecture"
Cohesion: 0.08
Nodes (24): ADR-003: Screener Architecture, Attention Allocation Policy, Consequences, Context, Decision, Demotion (to lower tier), Non-Goals (V1), Promotion / Demotion Policy (+16 more)

### Community 13 - "ConnectionStatus"
Cohesion: 0.20
Nodes (7): ExchangeConnection, Any, Base class for exchange WebSocket connections.      Subclasses define _connect_a, ConnectionStatus, datetime, Exchange connection state change., TestEventBus

### Community 14 - "ADR-010: Edge Engine Framework"
Cohesion: 0.08
Nodes (23): ADR-010: Edge Engine Framework, Aggregated Output, Aggregation Rules, Aggregation Type, Architecture, Components, Config, Consequences (+15 more)

### Community 15 - "ADR-005: Feature Normalization"
Cohesion: 0.09
Nodes (22): ADR-005: Feature Normalization, Architecture, Components, Composite Normalized Score, Consequences, Consumer Map, Context, Decision (+14 more)

### Community 16 - "ADR-008: Tier Assignment"
Cohesion: 0.09
Nodes (22): ADR-008: Tier Assignment, Capacity Enforcement, Capacity rationale, Config, Consequences, Consumer Map, Context, Decision (+14 more)

### Community 17 - "EventBus"
Cohesion: 0.15
Nodes (5): EventBus, Async priority-based pub/sub bus.      - High-priority events (trade, liquidatio, Start the delivery loop., MockExchangeConnection, TestExchangeConnection

### Community 18 - "SPEC-Research-Lifecycle"
Cohesion: 0.10
Nodes (20): Alpha Attribution, Automatic Revalidation, Certification Committee, Forward Test Requirement, Gate 1: BACKTEST → PAPER_VALIDATED, Gate 2: PAPER_VALIDATED → FORWARD_TEST, Gate 3: FORWARD_TEST → CERTIFIED, Gate 4: CERTIFIED → PRODUCTION (+12 more)

### Community 19 - "SPEC-Special-Situations"
Cohesion: 0.10
Nodes (20): Cooldown Table, Detection Contract, Detection Pipeline, Expiration & Cleanup, Metrics, Opportunity Queue Integration, OpportunityCandidate (Queue Entry), Principles (+12 more)

### Community 20 - "SPEC-Screener"
Cohesion: 0.11
Nodes (18): Budget Breakdown (edge path), Daily Operational Target, Degradation Modes, Dependencies, Desktop (i3 Gen13 + GTX 1660 Ti), Failure Handling, Hardware Profiles, Jetson Nano 2GB (+10 more)

### Community 21 - "SPEC-Sector-Classification"
Cohesion: 0.11
Nodes (18): Auto-Review, Breadth Integration, Classification Contract, Classification Lifecycle, Classification Output, Constraints, Leader Selection Criteria, Metrics (+10 more)

### Community 22 - "Sub-Objects"
Cohesion: 0.11
Nodes (18): Access Patterns, AttentionRecord, BreadthContext, Concurrency, EdgeResult, FeatureValue, JSON Serialization (Wire Format), MarketSnapshot (+10 more)

### Community 23 - "api.ts"
Cohesion: 0.18
Nodes (13): SymbolRegistry(), SymbolRegistryData, SymbolDetailDrawer(), columns, helper, SymbolRow, ExchangeInfo, fetcher() (+5 more)

### Community 24 - "ADR-002: Market Data Layer"
Cohesion: 0.11
Nodes (17): Adapter Responsibilities, ADR-002: Market Data Layer, Architecture, Connection Strategy, Consequences, Context, Decision, Design Answers (+9 more)

### Community 25 - "Event"
Cohesion: 0.23
Nodes (11): build_subscribe(), _extract_payload(), parse_message(), _parse_ts(), Any, datetime, Bybit Futures WS message adapter — parses V5 public linear streams.  Produces Ma, Convert ms timestamp to UTC datetime. (+3 more)

### Community 26 - "__init__.py"
Cohesion: 0.06
Nodes (44): BreadthEngine, ADR-006 Breadth Engine.  Computes market-wide breadth indicators from normalized, Return fresh RawFeature or None if stale / missing., FeatureUpdateEvent, MarketBreadth, NormalizedFeature, NormalizedFeatureUpdateEvent, RankedSymbol (+36 more)

### Community 27 - "ADR-004: Feature Store"
Cohesion: 0.12
Nodes (15): ADR-004: Feature Store, Architecture, Consequences, Context, Data Flow Detail, Decision, Design Answers, Feature Data Model (+7 more)

### Community 28 - "Exit Criteria per Fase"
Cohesion: 0.12
Nodes (15): Aturan, Exit Criteria per Fase, Fase, Phase 10 — Paper Trading, Phase 11 — Execution, Phase 1 — Market Data Layer, Phase 2 — Feature Store, Phase 3 — Normalization (+7 more)

### Community 29 - "References — Open Source Architecture Study"
Cohesion: 0.12
Nodes (15): Catatan, Cryptofeed, EarnHFT, FinRL, Freqtrade, Hummingbot, Jesse, Mapping per Dokumen (+7 more)

### Community 30 - "EDGE-Certification"
Cohesion: 0.13
Nodes (14): Auto-Disable, Certification Framework, Certification Status Summary, Certification Template, Certification Thresholds, Certifications, E001 — OI Breakout, E002 — Funding Reversal (+6 more)

### Community 31 - "Certifications"
Cohesion: 0.13
Nodes (14): Certification Framework, Certification Status Summary, Certification Template, Certifications, F001 — Liquidity, F002 — OI Expansion, F003 — Volume Expansion, F004 — RS (Relative Strength) (+6 more)

### Community 32 - "FEATURE-Registry"
Cohesion: 0.13
Nodes (14): Adding a New Feature, F001 — Liquidity, F002 — OI Expansion, F003 — Volume Expansion, F004 — RS (Relative Strength), F005 — Compression, F006 — Funding Rate, Feature Categories (+6 more)

### Community 33 - "EDGE-Registry"
Cohesion: 0.14
Nodes (13): Adding a New Edge, E001 — OI Breakout, E002 — Funding Reversal, E003 — Volume Momentum, E004 — Compression Breakout, E005 — Leader Follower, Edge Details, Edge Families (+5 more)

### Community 34 - "binance.py"
Cohesion: 0.21
Nodes (13): build_subscribe(), _extract_payload(), heartbeat(), parse_message(), _parse_ts(), Any, datetime, Binance Futures WS message adapter — parses USDⓈ-M streams.  Produces MarketEven (+5 more)

### Community 35 - "AGENT GUIDELINES"
Cohesion: 0.15
Nodes (12): AGENT GUIDELINES, Common Queries, Domain-Specific Extensions, Forbidden, Graph Node Types, Graphify Knowledge Graph, Pipeline Rules, Ponytail Ladder (DietrichGebert/ponytail) (+4 more)

### Community 36 - "EventType"
Cohesion: 0.20
Nodes (10): ABC, Enum, Exchange connection — base class for WS connections with reconnect.  Emits Conne, Priority event bus — pub/sub with ordered delivery per symbol., EventType, Event schemas — Phase 1 contract (frozen).  Hierarchy:   Event (base, all events, Registry lifecycle event — symbol added or removed., SymbolEvent (+2 more)

### Community 37 - "TestSequenceValidator"
Cohesion: 0.19
Nodes (5): TestSequenceValidator, Sequence Validator — detect gaps, duplicates, out-of-order per symbol.  Uses Exc, Per-exchange, per-symbol sequence tracking.      Detects:     - Missing sequence, Check sequence anomaly. Returns anomaly type or None., SequenceValidator

### Community 38 - "ADR-001: System Overview"
Cohesion: 0.18
Nodes (10): ADR-001: System Overview, Consequences, Context, Core Principles, Data Flow, Decision, Goals, High-Level Pipeline (+2 more)

### Community 39 - "Aktif"
Cohesion: 0.18
Nodes (10): Aktif, H001 — OI Expansion precedes breakout, H002 — Volume momentum continuation, H003 — Funding extreme mean reversion, H004 — Compression breakout, H005 — Leader moves first, follower catches up, H006 — Compression P90 (REJECTED), MARKET-HYPOTHESES (+2 more)

### Community 40 - "SPEC-Signal-Attribution"
Cohesion: 0.18
Nodes (10): Alpha Source Resolution, Attribution Chain, Field Definitions, Non-Goals (V1), PnL Analysis Queries, Purpose, References, Signal Output Schema (+2 more)

### Community 41 - "Timestamps"
Cohesion: 0.33
Nodes (8): Triple-timestamp envelope per ADR-002 and ADR-004., Timestamps, enrich_timestamps(), _ensure_dt(), datetime, Timestamp enrichment helpers — attach exchange_ts, received_ts, processed_ts.  U, Set event.timestamps.      - If event already has timestamps, update exchange_ts, Normalise float timestamp to UTC datetime.

### Community 42 - "page.tsx"
Cohesion: 0.36
Nodes (5): ExchangeStatus, SystemOverview(), SystemStatus, StatusCard(), useWebSocket()

### Community 43 - "ALPHA-SOURCES"
Cohesion: 0.25
Nodes (7): A001 — OI Expansion, A002 — Volume Expansion, A008 — Sector Breadth, ALPHA-SOURCES, Cara Pakai, Detail, Sumber Alpha

### Community 44 - "Detail"
Cohesion: 0.25
Nodes (7): Cara Pakai, Detail, Priority Order, RESEARCH-BACKLOG, RND-001 — Leader/Follower Propagation, RND-002 — Sector Rotation Detection, RND-009 — Adaptive Attention Weights

### Community 45 - "layout.tsx"
Cohesion: 0.33
Nodes (4): inter, metadata, links, Navbar()

### Community 46 - "SYSTEM-CONSTRAINTS"
Cohesion: 0.29
Nodes (6): Cara Pakai, Desktop, Hard Limits (semua profile), Jetson Nano 2GB, Low VPS (2 vCPU, 4GB RAM), SYSTEM-CONSTRAINTS

### Community 47 - "TECH-DEBT"
Cohesion: 0.40
Nodes (4): Active, Cara Pakai, Resolved, TECH-DEBT

### Community 48 - "DECISION-LOG"
Cohesion: 0.50
Nodes (3): Cara Pakai, DECISION-LOG, Log

### Community 71 - "PerSymbolOrderedBus"
Cohesion: 0.18
Nodes (4): Handler, PerSymbolOrderedBus, Wraps EventBus with per-symbol ordering guarantee., Register a handler. events/symbols set = filter; None = all.

### Community 74 - "api.py"
Cohesion: 0.08
Nodes (19): bind_normalization(), bind_store(), feature_status(), handler_activity(), normalized_status(), normalized_symbol(), Observability — FeatureStore health + per-symbol feature dump.  Mounted as sub-r, High-level system health snapshot. (+11 more)

### Community 76 - "Event"
Cohesion: 0.24
Nodes (7): PrioritizedEvent, Enqueue a normalised event for delivery., Event, Base event — every system event carries these., Tests for Market Data Layer — no exchange connection needed., TestPrioritizedEvent, TestTimestamps

## Knowledge Gaps
- **498 isolated node(s):** `inter`, `metadata`, `SymbolDetail`, `ExchangeStatus`, `SystemStatus` (+493 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **13 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Exchange` connect `Exchange` to `MarketEvent`, `binance.py`, `EventType`, `TestSequenceValidator`, `api.py`, `Event`, `ConnectionStatus`, `EventBus`, `Event`, `__init__.py`?**
  _High betweenness centrality (0.031) - this node is a cross-community bridge._
- **Why does `EventBus` connect `EventBus` to `MarketEvent`, `EventType`, `TestSequenceValidator`, `PerSymbolOrderedBus`, `Exchange`, `api.py`, `Event`, `ConnectionStatus`, `__init__.py`?**
  _High betweenness centrality (0.028) - this node is a cross-community bridge._
- **Why does `MarketEvent` connect `MarketEvent` to `binance.py`, `EventType`, `TestSequenceValidator`, `PerSymbolOrderedBus`, `api.py`, `Event`, `ConnectionStatus`, `EventBus`, `Event`?**
  _High betweenness centrality (0.022) - this node is a cross-community bridge._
- **Are the 27 inferred relationships involving `MarketEvent` (e.g. with `FeatureHandler` and `FeatureStore`) actually correct?**
  _`MarketEvent` has 27 INFERRED edges - model-reasoned connections that need verification._
- **Are the 20 inferred relationships involving `Exchange` (e.g. with `FeatureHandler` and `FeatureStore`) actually correct?**
  _`Exchange` has 20 INFERRED edges - model-reasoned connections that need verification._
- **Are the 20 inferred relationships involving `EventBus` (e.g. with `BreadthEngine` and `FeatureHandler`) actually correct?**
  _`EventBus` has 20 INFERRED edges - model-reasoned connections that need verification._
- **Are the 24 inferred relationships involving `FeatureId` (e.g. with `BreadthEngine` and `FeatureHandler`) actually correct?**
  _`FeatureId` has 24 INFERRED edges - model-reasoned connections that need verification._