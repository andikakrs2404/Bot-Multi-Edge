# Graph Report - future-trading-bot-rnd  (2026-07-31)

## Corpus Check
- 147 files · ~70,692 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2004 nodes · 4019 edges · 123 communities (107 shown, 16 thin omitted)
- Extraction: 81% EXTRACTED · 19% INFERRED · 0% AMBIGUOUS · INFERRED: 783 edges (avg confidence: 0.53)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `6dff2bc4`
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
- Edge
- rules.py
- api.py
- contracts.py
- Event
- feature_factory.py
- raw_data_engine.py
- Dataset
- validation.py
- Feature
- UniverseDefinition
- Specification: AKB Representation
- Decision
- Decision
- validate_raw_observation
- ADR-007: Experiment Protocol
- Specification: Raw Data Engine
- Tables
- ADR-000: Vision, Philosophy, and Invariants
- ADR-001A: Decision Record Protocol
- ADR-005: Registry Model (Feature & Label)
- ADR-006: Rule Grammar (AST)
- ADR-008: Evidence Model
- ADR-009: AKB Representation
- Specification: Experiment Protocol
- Specification: Feature Factory
- validate_manifest
- ADR-000B: System Boundaries & Trust Model
- ADR-003: Data Contract
- ADR-004: Dataset Versioning
- Specification: Registry Model
- AlphaOS Constitutional Package
- Specification: Evidence Model
- Specification: Rule Grammar (AST)
- TestLabels
- ADR-000A: Ubiquitous Language
- ADR-001: Engineering Principles
- ADR-001B: Architectural Quality Attributes
- README.md
- Specification: Experiment Protocol (Field-Level)
- Specification: Raw & Snapshot Contracts
- Specification: Domain Entities (Field-Level)
- main.cpp
- glossary.md
- __init__.py
- FeatureStore
- registry.py
- Specification: Validator Engine
- Timestamps
- TestLabels
- .promote

## God Nodes (most connected - your core abstractions)
1. `Edge` - 70 edges
2. `MarketEvent` - 64 edges
3. `AKB` - 60 edges
4. `Exchange` - 56 edges
5. `EdgeRegistry` - 53 edges
6. `EventBus` - 46 edges
7. `Dataset` - 45 edges
8. `Evidence` - 45 edges
9. `FeatureId` - 44 edges
10. `EdgeStatus` - 43 edges

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

## Communities (123 total, 16 thin omitted)

### Community 0 - "MarketEvent"
Cohesion: 0.10
Nodes (41): ADR-006 Breadth Engine.  Computes market-wide breadth indicators from normalized, FeatureStore — authoritative state owner per ADR-004.  Ingest → route → handler, CandleHandler, _feature(), FeatureHandler, FundingHandler, LiquidationHandler, OpenInterestHandler (+33 more)

### Community 1 - "ObservabilityStore"
Cohesion: 0.06
Nodes (30): BaseModel, deque, FastAPI, _lifespan(), Observability API — FastAPI app with CORS.  Wires up pipeline EventBus, SymbolRe, ExchangeStatus, Pydantic response models for observability API., SymbolListResponse (+22 more)

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
Cohesion: 0.09
Nodes (17): FeatureHandler, Protocol, DefaultWindowManager, Protocol, Manages time-based data windows for various market data types     on a per-symbo, Default implementation of WindowManager.      Manages data windows for each symb, WindowManager, MarketEvent (+9 more)

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
Cohesion: 0.05
Nodes (33): ABC, Handler, ExchangeConnection, Any, Exchange connection — base class for WS connections with reconnect.  Emits Conne, Base class for exchange WebSocket connections.      Subclasses define _connect_a, EventBus, PerSymbolOrderedBus (+25 more)

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
Cohesion: 0.08
Nodes (41): Logical AST expression over Features (ADR-006)., Rule, _build_context(), Candidate, candidate_id(), CandidateStatus, _eval_row(), Evidence (+33 more)

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
Cohesion: 0.08
Nodes (27): BreadthEngine, MarketBreadth, NormalizedFeature, NormalizedFeatureUpdateEvent, RankedSymbol, One normalised feature value for one symbol., Notification of a normalized feature state change., Snapshot of market-wide conditions. (+19 more)

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
Cohesion: 0.10
Nodes (20): EventType, Exchange, datetime, Enum, str, Event schemas — Phase 1 contract (frozen).  Hierarchy:   Event (base, all events, Registry lifecycle event — symbol added or removed., SymbolEvent (+12 more)

### Community 35 - "AGENT GUIDELINES"
Cohesion: 0.15
Nodes (12): AGENT GUIDELINES, Common Queries, Domain-Specific Extensions, Forbidden, Graph Node Types, Graphify Knowledge Graph, Pipeline Rules, Ponytail Ladder (DietrichGebert/ponytail) (+4 more)

### Community 36 - "EventType"
Cohesion: 0.13
Nodes (21): AKB, link_edge_evidence(), link_evidence_trace(), Evidence, AlphaOS AKB Representation (ADR-009).  AKB = knowledge graph contract. Storage i, Add Edge → Evidence 1:N relationship and keep Edge.supported_by in sync., Add Evidence → Candidate and Evidence → Experiment relationships., Reject decisions that cannot trace to at least one ACTIVE Edge. (+13 more)

### Community 37 - "TestSequenceValidator"
Cohesion: 0.24
Nodes (15): ActivationEngine, ActivationPolicy, ActivationRecord, DecayRecord, Evidence, AlphaOS Activation Engine: VALIDATED → ACTIVE.  The formal gatekeeper between Re, Edge, Validated Candidate promoted to Knowledge (ADR-002/002A).      supported_by: 1:N (+7 more)

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
Cohesion: 0.17
Nodes (13): build_universe(), default_universe(), _is_leveraged(), Enum, str, AlphaOS Universe Definition (ADR-003/004, spec raw-data-engine §4).  Universe is, Reproducible universe selection (spec §4)., Deterministic universe id = SHA256(canonical definition). (+5 more)

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
Cohesion: 0.30
Nodes (5): Validate one raw observation row (trust level 0)., validate_raw_observation(), good_row(), TestAssertValid, TestRawObservation

### Community 72 - "Edge"
Cohesion: 0.08
Nodes (24): KeyError, EvidenceRegistry, Evidence registry (ADR-005 kernel, spec §4)., Advance evidence lifecycle (spec §3): GENERATED → REVIEWED → SUPPORTS|REFUTES., review(), Advance Edge lifecycle in place (Portfolio/monitoring stages use this)., ValueError, Register a new entry. Fails on duplicate ACTIVE identity. (+16 more)

### Community 73 - "rules.py"
Cohesion: 0.10
Nodes (29): FeatureContext, And, canonical_text(), canonicalize(), _compare(), Comparison, evaluate(), Expr (+21 more)

### Community 74 - "api.py"
Cohesion: 0.25
Nodes (10): GraphRelationship, NodeType, Enum, str, EdgeStatus, PortfolioStatus, Enum, str (+2 more)

### Community 75 - "contracts.py"
Cohesion: 0.15
Nodes (18): assert_trust(), DatasetStatus, Experiment, ExperimentStatus, Feature, Immutable derived property of market state (ADR-005)., Reproducible scientific inquiry (ADR-007)., First-class knowledge graph edge (ADR-002). (+10 more)

### Community 76 - "Event"
Cohesion: 0.28
Nodes (11): EdgeRegistry, Edge registry — living entities with lifecycle., Promote SUPPORTS Evidence into VALIDATED Edge., ValidationPolicy, ValidatorEngine, build_akb(), make_evidence(), Evidence (+3 more)

### Community 77 - "feature_factory.py"
Cohesion: 0.12
Nodes (21): label_series_flat(), AlphaOS Feature Factory (ADR-000B/002/003/005, spec feature-factory).  Dataset (, Compute a flat label series from OHLCV (research)., atr_percent(), compute_feature(), compute_label(), ema(), pct_change() (+13 more)

### Community 78 - "raw_data_engine.py"
Cohesion: 0.17
Nodes (15): fetch_24h_volume_map(), fetch_funding(), fetch_klines(), fetch_open_interest(), FetchStats, _get_json(), Binance Futures fetcher (Raw Data Engine input layer).  Stdlib only: urllib for, OI history (futures data endpoint), paginated by startTime. (+7 more)

### Community 79 - "Dataset"
Cohesion: 0.23
Nodes (10): FeatureFactory, FeatureFactoryError, Path, RuntimeError, Builds FeatureSnapshots (trust level 2) from registered datasets., make_registry(), Create a minimal registered klines dataset on disk., seed_dataset() (+2 more)

### Community 80 - "validation.py"
Cohesion: 0.11
Nodes (22): Build a FeatureSnapshot from a registered dataset. Returns snapshot_id., Re-verify a dataset artifact (spec §9): manifest + id + content hash., verify_dataset(), assert_valid(), check_dataset_id(), content_hash_of(), ContractViolation, dataset_id_of() (+14 more)

### Community 81 - "Feature"
Cohesion: 0.17
Nodes (10): FeatureRegistry, Feature + Label registry (same kernel, kind discriminator)., make_dataset(), make_edge(), make_feature(), make_rule(), Tests for AlphaOS Registry Kernel (ADR-005).  Spec: docs/specifications/registry, TestConcreteRegistries (+2 more)

### Community 82 - "UniverseDefinition"
Cohesion: 0.22
Nodes (6): content_hash(), make_dataset_id(), make_id(), make_rule_id(), SHA256 over the canonical JSON serialization of an object., Deterministic id from parts (permanent identity).

### Community 83 - "Specification: AKB Representation"
Cohesion: 0.14
Nodes (13): 1. Purpose, 2. Node Types, 3. Relationship Types, 4.1 Edge evidence is 1:N, 4.2 Evidence traceability, 4.3 Production traceability, 4.4 No orphan knowledge, 4. Core Graph Guarantees (+5 more)

### Community 84 - "Decision"
Cohesion: 0.15
Nodes (12): ADR-002: Domain Ontology, Alternatives Considered, Consequences, Context, Core Entities, Decision, Domain Axioms, Domain Invariants (+4 more)

### Community 85 - "Decision"
Cohesion: 0.15
Nodes (12): ADR-002A: Domain Lifecycles, Alternatives Considered, Consequences, Context, Dataset, Decision, Edge, Experiment (+4 more)

### Community 86 - "validate_raw_observation"
Cohesion: 0.21
Nodes (13): build_subscribe(), _extract_payload(), heartbeat(), parse_message(), _parse_ts(), Any, datetime, Binance Futures WS message adapter — parses USDⓈ-M streams.  Produces MarketEven (+5 more)

### Community 87 - "ADR-007: Experiment Protocol"
Cohesion: 0.17
Nodes (11): ADR-007: Experiment Protocol, Alternatives Considered, Anti-Overfitting Doctrine, Consequences, Context, Decision, Execution Rules, ExperimentConfig (declared BEFORE execution) (+3 more)

### Community 88 - "Specification: Raw Data Engine"
Cohesion: 0.17
Nodes (11): 10. Testing, 1. Scope Boundary, 2. Inputs, 3. Outputs (artifacts), 4. Universe Definition (artifact, not hardcoded), 5. Manifest (minimal), 6. Downloader Requirements, 7. Validation Pipeline (ADR-003) (+3 more)

### Community 89 - "Tables"
Cohesion: 0.17
Nodes (11): Access Rules, edges, evidence_bundles, experiments, knowledge_graph (relationship edges), portfolios, production_decisions, registries (+3 more)

### Community 90 - "ADR-000: Vision, Philosophy, and Invariants"
Cohesion: 0.18
Nodes (10): ADR-000: Vision, Philosophy, and Invariants, Alternatives Considered, Architectural Invariants (Unbreakable), Consequences, Context, Decision, Migration Path, Non-Goals (+2 more)

### Community 91 - "ADR-001A: Decision Record Protocol"
Cohesion: 0.18
Nodes (10): ADR-001A: Decision Record Protocol, ADR Status Lifecycle, Alternatives Considered, Consequences, Constitutional Freeze Protocol, Constitutional Scope Lock, Context, Decision (+2 more)

### Community 92 - "ADR-005: Registry Model (Feature & Label)"
Cohesion: 0.18
Nodes (10): ADR-005: Registry Model (Feature & Label), Alternatives Considered, Consequences, Context, Decision, Governance, Identity & Evolution, Migration Path (+2 more)

### Community 93 - "ADR-006: Rule Grammar (AST)"
Cohesion: 0.18
Nodes (10): ADR-006: Rule Grammar (AST), Alternatives Considered, AST Supremacy, Canonical Form & Identity, Consequences, Context, Decision, Grammar (+2 more)

### Community 94 - "ADR-008: Evidence Model"
Cohesion: 0.18
Nodes (10): ADR-008: Evidence Model, Alternatives Considered, Consequences, Context, Decision, Evidence Components, Evidence Definition, Immutability & Attachment (+2 more)

### Community 95 - "ADR-009: AKB Representation"
Cohesion: 0.18
Nodes (10): ADR-009: AKB Representation, Alternatives Considered, Concurrency & Access, Consequences, Context, Decision, Logical Structure, Migration Path (+2 more)

### Community 96 - "Specification: Experiment Protocol"
Cohesion: 0.18
Nodes (10): 1. Purpose, 2. Experiment Identity (Fingerprint), 3. Experiment Fields, 4. Lifecycle, 5. Candidate, 6. Evidence, 7. Evaluation Semantics, 8. Artifacts (+2 more)

### Community 97 - "Specification: Feature Factory"
Cohesion: 0.18
Nodes (10): 1. Trust Level, 2. Inputs, 3. Outputs, 4. Feature Computation, 5. Labels (research datasets only), 6. Snapshot Manifest, 7. Registration, 8. Acceptance Criteria (+2 more)

### Community 98 - "validate_manifest"
Cohesion: 0.20
Nodes (9): _dedupe_nodes(), GraphNode, Any, Given EvidenceID → Candidate and Experiment., Given EdgeID → Dataset(s) via Evidence → Experiment → Dataset., Given RuleID → Experiments using it., ProductionDecision → Portfolio → Edge → Evidence → Experiment → Dataset., Reject orphan ACTIVE Edge (spec §4.4). (+1 more)

### Community 99 - "ADR-000B: System Boundaries & Trust Model"
Cohesion: 0.20
Nodes (9): ADR-000B: System Boundaries & Trust Model, Alternatives Considered, Consequences, Context, Decision, Migration Path, System Boundaries, Trust Invariant (+1 more)

### Community 100 - "ADR-003: Data Contract"
Cohesion: 0.20
Nodes (9): ADR-003: Data Contract, Alternatives Considered, Consequences, Context, Contract Taxonomy, Decision, Field-Level Schemas, Migration Path (+1 more)

### Community 101 - "ADR-004: Dataset Versioning"
Cohesion: 0.20
Nodes (9): Access Rule, ADR-004: Dataset Versioning, Alternatives Considered, Consequences, Context, Decision, Identity, Migration Path (+1 more)

### Community 102 - "Specification: Registry Model"
Cohesion: 0.20
Nodes (9): 1. Purpose, 2. Registry Entry, 3. Registry Status, 4. Version Rules, 5. Supersession Rules, 6. Lookup Semantics, 7. Validation, 8. Kinds (+1 more)

### Community 103 - "AlphaOS Constitutional Package"
Cohesion: 0.22
Nodes (8): AlphaOS Constitutional Package, Architectural Hash (FINAL), Freeze Declaration, Included ADRs, Layer 0 — Constitution, Layer 1 — Domain & Contracts, Purpose, Ratification Checklist

### Community 104 - "Specification: Evidence Model"
Cohesion: 0.22
Nodes (8): 1. Purpose, 2. Evidence Record, 3. Lifecycle, 4. Registry, 5. Acceptance Criteria (Validator stage defaults), 6. Retention, 7. Acceptance Criteria (this stage), Specification: Evidence Model

### Community 105 - "Specification: Rule Grammar (AST)"
Cohesion: 0.22
Nodes (8): 1. Representation, 2. Node Types, 3. Canonical Form, 4. Identity, 5. Evaluation, 6. Registration Requirement, Canonical Text Format, Specification: Rule Grammar (AST)

### Community 106 - "TestLabels"
Cohesion: 0.11
Nodes (22): Evidence, datetime, AlphaOS shared contracts (ADR-002/003/004/005).  Constitution hash: be37bf975086, Statistical results supporting/refuting a Candidate (ADR-008)., utcnow(), evidence_id(), EvidenceStatus, Enum (+14 more)

### Community 107 - "ADR-000A: Ubiquitous Language"
Cohesion: 0.29
Nodes (6): ADR-000A: Ubiquitous Language, Alternatives Considered, Consequences, Context, Decision, Migration Path

### Community 108 - "ADR-001: Engineering Principles"
Cohesion: 0.29
Nodes (6): ADR-001: Engineering Principles, Alternatives Considered, Consequences, Context, Decision, Migration Path

### Community 109 - "ADR-001B: Architectural Quality Attributes"
Cohesion: 0.29
Nodes (6): ADR-001B: Architectural Quality Attributes, Alternatives Considered, Consequences, Context, Decision, Migration Path

### Community 110 - "README.md"
Cohesion: 0.29
Nodes (6): AlphaOS Architectural Decision Records (ADRs), Constitutional Package v1.0, Dependency Rules, Layer 0 — Constitution, Layer 1 — Domain & Contracts, Supporting Documents

### Community 111 - "Specification: Experiment Protocol (Field-Level)"
Cohesion: 0.29
Nodes (6): Anti-Overfitting (mandatory steps), CandidateResult, Canonical Metrics (computed identically everywhere), ExperimentConfig, Minimum Viability Thresholds (v1.0), Specification: Experiment Protocol (Field-Level)

### Community 112 - "Specification: Raw & Snapshot Contracts"
Cohesion: 0.33
Nodes (5): FeatureSnapshot Contract (Trust Level 2), Manifest (per Dataset), Raw Observation Contracts (Trust Level 0), Specification: Raw & Snapshot Contracts, Validation Rules

### Community 113 - "Specification: Domain Entities (Field-Level)"
Cohesion: 0.33
Nodes (5): EdgeRecord, Lifecycle Transition Log, PortfolioRecord, ProductionDecisionRecord, Specification: Domain Entities (Field-Level)

### Community 114 - "main.cpp"
Cohesion: 0.25
Nodes (6): DatasetResult, Full pipeline for one dataset type over one universe (spec §3)., _to_ms(), _to_table(), _validate_rows(), Table

### Community 117 - "FeatureStore"
Cohesion: 0.07
Nodes (20): bind_normalization(), bind_store(), feature_status(), handler_activity(), normalized_status(), normalized_symbol(), Observability — FeatureStore health + per-symbol feature dump.  Mounted as sub-r, High-level system health snapshot. (+12 more)

### Community 118 - "registry.py"
Cohesion: 0.16
Nodes (21): FetchError, RuntimeError, Non-retryable fetch failure., Dataset, Immutable, versioned collection of market data (ADR-002, ADR-004)., EngineError, RuntimeError, Orchestrator: download → validate → artifacts → register (spec §3,§8). (+13 more)

### Community 119 - "Specification: Validator Engine"
Cohesion: 0.20
Nodes (9): 1. Purpose, 2. Input Contract, 3. ValidationPolicy, 4. Edge Creation, 5. Edge Lifecycle, 6. Registry, 7. AKB Integration, 8. Acceptance Criteria (+1 more)

### Community 120 - "Timestamps"
Cohesion: 0.25
Nodes (7): 1. Purpose, 2. ActivationPolicy, 3. ActivationRecord, 4. Edge Lifecycle Transitions, 5. AKB Integration, 6. Acceptance Criteria, Specification: Activation Engine

### Community 121 - "TestLabels"
Cohesion: 0.36
Nodes (3): label_series(), Single label series (flat)., TestLabels

## Knowledge Gaps
- **718 isolated node(s):** `inter`, `metadata`, `SymbolDetail`, `ExchangeStatus`, `SystemStatus` (+713 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **16 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Exchange` connect `binance.py` to `MarketEvent`, `Exchange`, `ConnectionStatus`, `FeatureStore`, `validate_raw_observation`, `Event`, `__init__.py`?**
  _High betweenness centrality (0.037) - this node is a cross-community bridge._
- **Why does `TestRankingEngine` connect `__init__.py` to `MarketEvent`, `EventBus`, `binance.py`?**
  _High betweenness centrality (0.036) - this node is a cross-community bridge._
- **Why does `Registry` connect `EventBus` to `TestSequenceValidator`, `Edge`, `TestLabels`, `Event`, `feature_factory.py`, `raw_data_engine.py`, `Dataset`, `Feature`, `main.cpp`, `registry.py`?**
  _High betweenness centrality (0.030) - this node is a cross-community bridge._
- **Are the 38 inferred relationships involving `Edge` (e.g. with `ActivationEngine` and `ActivationPolicy`) actually correct?**
  _`Edge` has 38 INFERRED edges - model-reasoned connections that need verification._
- **Are the 27 inferred relationships involving `MarketEvent` (e.g. with `FeatureHandler` and `FeatureStore`) actually correct?**
  _`MarketEvent` has 27 INFERRED edges - model-reasoned connections that need verification._
- **Are the 22 inferred relationships involving `AKB` (e.g. with `ActivationEngine` and `ActivationPolicy`) actually correct?**
  _`AKB` has 22 INFERRED edges - model-reasoned connections that need verification._
- **Are the 20 inferred relationships involving `Exchange` (e.g. with `FeatureHandler` and `FeatureStore`) actually correct?**
  _`Exchange` has 20 INFERRED edges - model-reasoned connections that need verification._