# ADR-001: System Overview

**Status:** DRAFT  
**Date:** 2026-07-27  
**Author:** Lead Architect  
**Deciders:** Lead Architect  

---

## Context

Trading futures across multiple exchanges with 500–1000+ symbols requires a scalable, event-driven architecture. Direct per-symbol polling or monolithic feature computation does not scale. Every architectural decision must anticipate 3 exchanges, 20+ edge strategies, and zero-downtime feature addition.

## Decision

Adopt a **layered, event-driven screener pipeline** with single-pass feature computation and exchange-agnostic normalized data.

## Goals

| Goal | Description |
|------|-------------|
| **Exchanges** | Bybit Futures, Binance Futures (extensible to others) |
| **Universe** | 500–1000 symbols |
| **Feature Discovery** | Compute features once, consume by all edges |
| **Attention Allocation** | Tier-based focus; compute resources on high-signal symbols |
| **Edge Detection** | Run N edge strategies on focused queue |
| **Scalping** | Sub-second decision path for hot symbols |
| **Market Context** | Global market breadth and sector breadth monitoring |
| **Replay Compatible** | All events can be replayed from store for backtest/validation |

## Core Principles

1. **Feature computed once** — no two edges recompute the same metric
2. **Event driven** — state changes propagate; no polling loops
3. **Exchange agnostic** — market data adapters normalise to common schema
4. **Replay compatible** — event store enables historical reconstruction
5. **Fail isolated** — one exchange adapter crash does not take down the system
6. **Explainable decisions** — every signal traceable to features & conditions that produced it
7. **Normalized features over raw values** — percentile/rank preferred (OI_PCTL=92 > OI=1.8%)

## High-Level Pipeline

```
Exchange
    │
    ▼
Market Data Layer          ┌──────────────────────────────┐
    │                       │  Special Situation Pipeline  │
    ▼                       │                              │
Metadata Layer              │  · New Listing               │
    │                       │  · Funding Extreme           │
    ▼                       │  · Liquidation Cascade       │
Feature Store               │  · Exchange Incident         │
    │                       │  · Massive OI Spike          │
    ▼                       │                              │
Feature Normalization       │         ▼                    │
    │                   Opportunity Queue                  │
    ▼                       └──────────────────────────────┘
Market Breadth
    │
    ▼
Attention Allocation
    │
    ▼
Focus Queue
    │
    ▼
Edge Engine
    │
    ▼
Execution
```

**Two parallel paths:**
- **Main Pipeline:** Metadata → Feature → Normalize → Breadth → Attention → Focus → Edge
- **Special Situation:** Detects events that bypass attention (new listing, funding spike, etc.) → Opportunity Queue

## Data Flow

1. Exchange WS feeds → Market Data Adapters → **normalised events**
2. Normalised events → **Metadata Layer** → enrich with listing age, sector, market cap tier
3. Enriched events → **Feature Store** → **feature values computed once**
4. Feature values → **Feature Normalization** → raw → percentile/rank per universe
5. Normalized features → **Market Breadth** → sector & global context (e.g. 72% above EMA20)
6. Features + Breadth → **Attention Engine** → **heat score** per symbol
7. Heat scores → Tier assignment → **Focus Queue** (top N by tier)
8. Focus Queue → **Edge Engine** → each edge reads shared normalized features
9. Edge signals → Execution layer

**Parallel:** Events also feed **Special Situation Detection Engine** → **Opportunity Queue** → direct to Edge Engine (bypasses Attention)

## Non-Goals (V1)

- Order execution / order management
- P&L tracking
- Backtesting engine (replay is seed for future)
- Risk management system

## Consequences

**Positive:**
- Adding new edge = write detection logic only, no feature recomputation
- Adding new exchange = write adapter only, rest of pipeline untouched
- Tier system ensures compute cost stays O(focus_size) not O(universe)
- Replay enables deterministic backtest from real market data

**Negative:**
- Event bus becomes critical path — latency on event propagation affects all consumers
- Feature Store must handle 500–1000 concurrent symbol states with sub-second updates
- Attention Engine design directly determines edge quality; bad tier config = missed signals

## References

- ADR-002: Market Data Layer
- ADR-003: Screener Architecture
- ADR-004: Feature Store
- ADR-005: Attention Allocation
