# Graph Report - future-trading-bot-rnd  (2026-07-31)

## Corpus Check
- 150 files · ~71,667 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2053 nodes · 4271 edges · 119 communities (101 shown, 18 thin omitted)
- Extraction: 79% EXTRACTED · 21% INFERRED · 0% AMBIGUOUS · INFERRED: 887 edges (avg confidence: 0.52)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `9e9a9b8e`
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
- glossary.md
- __init__.py
- FeatureStore
- registry.py
- Specification: Validator Engine
- Timestamps

## God Nodes (most connected - your core abstractions)
1. `Edge` - 77 edges
2. `AKB` - 74 edges
3. `EdgeRegistry` - 68 edges
4. `MarketEvent` - 64 edges
5. `Exchange` - 56 edges
6. `EdgeStatus` - 56 edges
7. `RelationshipType` - 48 edges
8. `EventBus` - 46 edges
9. `NodeType` - 46 edges
10. `Dataset` - 46 edges

## Surprising Connections (you probably didn't know these)
- `BreadthEngine` --uses--> `EventBus`  [INFERRED]
  features/breadth.py → market_data/event_bus.py
- `FeatureHandler` --uses--> `EventBus`  [INFERRED]
  features/feature_store.py → market_data/event_bus.py
- `FeatureHandler` --uses--> `EventType`  [INFERRED]
  features/feature_store.py → market_data/events.py
- `FeatureHandler` --uses--> `MarketEvent`  [INFERRED]
  features/feature_store.py → market_data/events.py
- `FeatureStore` --uses--> `EventBus`  [INFERRED]
  features/feature_store.py → market_data/event_bus.py

## Import Cycles
- None detected.

## Communities (119 total, 18 thin omitted)

### Community 0 - "MarketEvent"
Cohesion: 0.10
Nodes (41): CandleHandler, _feature(), FeatureHandler, FundingHandler, LiquidationHandler, OpenInterestHandler, Protocol, Feature handlers — one per event type, one handler_id per handler.  Each handler (+33 more)

### Community 1 - "ObservabilityStore"
Cohesion: 0.05
Nodes (42): BaseModel, deque, FastAPI, bind_normalization(), bind_store(), feature_status(), handler_activity(), normalized_status() (+34 more)

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
Cohesion: 0.13
Nodes (10): DefaultWindowManager, Default implementation of WindowManager.      Manages data windows for each symb, Verify SymbolWindowState is a dataclass with slots (no instance dict)., Verify DefaultWindowManager can be instantiated., Verify data is appended to the correct deques., Verify deques respect their maxlen., Verify state is isolated between different symbols., Verify all necessary components can be imported. (+2 more)

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
Nodes (38): ABC, Handler, ExchangeConnection, Any, Exchange connection — base class for WS connections with reconnect.  Emits Conne, Base class for exchange WebSocket connections.      Subclasses define _connect_a, EventBus, PerSymbolOrderedBus (+30 more)

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
Cohesion: 0.13
Nodes (27): _build_context(), Candidate, candidate_id(), CandidateStatus, _eval_row(), Evidence, evidence_id(), Experiment (+19 more)

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
Cohesion: 0.19
Nodes (5): TestSequenceValidator, Sequence Validator — detect gaps, duplicates, out-of-order per symbol.  Uses Exc, Per-exchange, per-symbol sequence tracking.      Detects:     - Missing sequence, Check sequence anomaly. Returns anomaly type or None., SequenceValidator

### Community 26 - "__init__.py"
Cohesion: 0.08
Nodes (24): BreadthEngine, ADR-006 Breadth Engine.  Computes market-wide breadth indicators from normalized, MarketBreadth, NormalizedFeature, NormalizedFeatureUpdateEvent, RankedSymbol, One normalised feature value for one symbol., Notification of a normalized feature state change. (+16 more)

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
Cohesion: 0.13
Nodes (9): _infer_sector(), Any, Strip quote suffix + numeric prefix, then match keywords., Auto-discovers symbols from exchange REST APIs.      - Polls every interval_sec, SymbolMeta, SymbolRegistry, _lifespan(), Lightweight query facade over SymbolRegistry.      No-op when no registry is att (+1 more)

### Community 35 - "AGENT GUIDELINES"
Cohesion: 0.15
Nodes (12): AGENT GUIDELINES, Common Queries, Domain-Specific Extensions, Forbidden, Graph Node Types, Graphify Knowledge Graph, Pipeline Rules, Ponytail Ladder (DietrichGebert/ponytail) (+4 more)

### Community 36 - "EventType"
Cohesion: 0.10
Nodes (20): link_edge_evidence(), link_evidence_trace(), Evidence, Add Edge → Evidence 1:N relationship and keep Edge.supported_by in sync., Add Evidence → Candidate and Evidence → Experiment relationships., Reject decisions that cannot trace to at least one ACTIVE Edge., register_production_decision(), Edge (+12 more)

### Community 37 - "TestSequenceValidator"
Cohesion: 0.06
Nodes (77): ActivationEngine, ActivationPolicy, ActivationRecord, DecayRecord, Evidence, AlphaOS Activation Engine: VALIDATED → ACTIVE.  The formal gatekeeper between Re, AKB, _dedupe_nodes() (+69 more)

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
Nodes (5): ExperimentRunner, Evaluate rules against a research snapshot; emit candidates+evidence., make_snapshot(), Research snapshot: one feature + label_HIT_TARGET.      RSI constructed so rule, TestRunner

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
Cohesion: 0.40
Nodes (4): matches(), Convenience: parse canonical text and evaluate., ctx(), TestEvaluation

### Community 72 - "Edge"
Cohesion: 0.10
Nodes (25): datetime, utcnow(), Enum, AlphaOS Evidence Model (ADR-008, spec evidence-model).  Evidence = immutable rec, DuplicateActiveError, Enum, str, ValueError (+17 more)

### Community 73 - "rules.py"
Cohesion: 0.11
Nodes (25): FeatureContext, And, canonical_text(), canonicalize(), _compare(), Comparison, evaluate(), Expr (+17 more)

### Community 74 - "api.py"
Cohesion: 0.22
Nodes (8): 1. Purpose, 2. Policy, 3. Contract, 4. Invariants, 5. Registry, 6. AKB Integration, 7. Acceptance Criteria, Specification: Portfolio

### Community 75 - "contracts.py"
Cohesion: 0.12
Nodes (29): assert_trust(), content_hash(), Dataset, DatasetStatus, Evidence, Experiment, ExperimentStatus, make_dataset_id() (+21 more)

### Community 77 - "feature_factory.py"
Cohesion: 0.09
Nodes (25): KeyError, label_series_flat(), AlphaOS Feature Factory (ADR-000B/002/003/005, spec feature-factory).  Dataset (, Compute a flat label series from OHLCV (research)., atr_percent(), compute_feature(), compute_label(), ema() (+17 more)

### Community 79 - "Dataset"
Cohesion: 0.20
Nodes (11): FeatureFactory, FeatureFactoryError, Path, RuntimeError, Builds FeatureSnapshots (trust level 2) from registered datasets., Build a FeatureSnapshot from a registered dataset. Returns snapshot_id., make_registry(), Create a minimal registered klines dataset on disk. (+3 more)

### Community 80 - "validation.py"
Cohesion: 0.09
Nodes (27): Re-verify a dataset artifact (spec §9): manifest + id + content hash., verify_dataset(), Deterministic universe id = SHA256(canonical definition)., assert_valid(), check_dataset_id(), content_hash_of(), ContractViolation, dataset_id_of() (+19 more)

### Community 81 - "Feature"
Cohesion: 0.12
Nodes (15): Feature, Immutable derived property of market state (ADR-005)., FeatureRegistry, Concrete AlphaOS registries (ADR-005, spec §8).  FeatureRegistry (kind feature|l, Feature + Label registry (same kernel, kind discriminator)., Rule registry — identity is the content-addressed RuleID., RuleRegistry, make_dataset() (+7 more)

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
Cohesion: 0.10
Nodes (27): build_subscribe(), _extract_payload(), heartbeat(), parse_message(), _parse_ts(), Any, datetime, Binance Futures WS message adapter — parses USDⓈ-M streams.  Produces MarketEven (+19 more)

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
Cohesion: 0.14
Nodes (12): evidence_id(), EvidenceRegistry, Deterministic EVID-ID (spec §2)., Evidence registry (ADR-005 kernel, spec §4)., Advance evidence lifecycle (spec §3): GENERATED → REVIEWED → SUPPORTS|REFUTES., review(), make_evidence(), Evidence (+4 more)

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

### Community 117 - "FeatureStore"
Cohesion: 0.10
Nodes (16): FeatureHandler, FeatureStore, Protocol, FeatureStore — authoritative state owner per ADR-004.  Ingest → route → handler, Return fresh RawFeature or None if stale / missing., Deprecated: use get_symbol_state(). Accepts str exchange for backward compat., Snapshot of store health., Authoritative state owner. Ingest, route, compute, store, notify. (+8 more)

### Community 118 - "registry.py"
Cohesion: 0.07
Nodes (50): fetch_24h_volume_map(), fetch_funding(), fetch_klines(), fetch_open_interest(), FetchError, FetchStats, _get_json(), RuntimeError (+42 more)

### Community 119 - "Specification: Validator Engine"
Cohesion: 0.20
Nodes (9): 1. Purpose, 2. Input Contract, 3. ValidationPolicy, 4. Edge Creation, 5. Edge Lifecycle, 6. Registry, 7. AKB Integration, 8. Acceptance Criteria (+1 more)

### Community 120 - "Timestamps"
Cohesion: 0.25
Nodes (7): 1. Purpose, 2. ActivationPolicy, 3. ActivationRecord, 4. Edge Lifecycle Transitions, 5. AKB Integration, 6. Acceptance Criteria, Specification: Activation Engine

## Knowledge Gaps
- **725 isolated node(s):** `inter`, `metadata`, `SymbolDetail`, `ExchangeStatus`, `SystemStatus` (+720 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **18 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Registry` connect `Edge` to `TestSequenceValidator`, `Timestamps`, `TestLabels`, `feature_factory.py`, `Dataset`, `EventBus`, `Feature`, `registry.py`?**
  _High betweenness centrality (0.048) - this node is a cross-community bridge._
- **Why does `Exchange` connect `FeatureStore` to `MarketEvent`, `ObservabilityStore`, `binance.py`, `Exchange`, `ConnectionStatus`, `validate_raw_observation`, `Event`, `__init__.py`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Why does `MarketEvent` connect `MarketEvent` to `Exchange`, `ConnectionStatus`, `FeatureStore`, `validate_raw_observation`, `Event`?**
  _High betweenness centrality (0.031) - this node is a cross-community bridge._
- **Are the 43 inferred relationships involving `Edge` (e.g. with `ActivationEngine` and `ActivationPolicy`) actually correct?**
  _`Edge` has 43 INFERRED edges - model-reasoned connections that need verification._
- **Are the 31 inferred relationships involving `AKB` (e.g. with `ActivationEngine` and `ActivationPolicy`) actually correct?**
  _`AKB` has 31 INFERRED edges - model-reasoned connections that need verification._
- **Are the 32 inferred relationships involving `EdgeRegistry` (e.g. with `ActivationEngine` and `ActivationPolicy`) actually correct?**
  _`EdgeRegistry` has 32 INFERRED edges - model-reasoned connections that need verification._
- **Are the 27 inferred relationships involving `MarketEvent` (e.g. with `FeatureHandler` and `FeatureStore`) actually correct?**
  _`MarketEvent` has 27 INFERRED edges - model-reasoned connections that need verification._