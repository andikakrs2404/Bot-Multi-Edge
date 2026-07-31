# Specification: Portfolio

Derived from: ADR-002 (Domain Ontology), ADR-002A (Domain Lifecycles), ADR-005 (Registry), ADR-009 (AKB)
Constitution: be37bf97... (Freeze v1.0, 2026-07-29)

Status: Draft (v0.1)

## 1. Purpose

Portfolio = immutable collection of ACTIVE Edges. It performs knowledge
selection only. It is not a risk engine, position-sizing engine,
execution layer, rebalance engine, or ProductionDecision.

## 2. Policy

```python
class WeightingMethod(Enum):
    EQUAL_WEIGHT = "equal_weight"

@dataclass(frozen=True)
class PortfolioPolicy:
    policy_id: str
    max_edges: int
    weighting_method: WeightingMethod
```

Only `EQUAL_WEIGHT` exists in this stage.

## 3. Contract

```python
@dataclass(frozen=True)
class Portfolio:
    portfolio_id: str
    policy_id: str
    edge_ids: tuple[str, ...]
    allocations: tuple[tuple[str, float], ...]
    status: PortfolioStatus
```

`edge_ids` are sorted. `allocations` are sorted by edge_id and sum to 1.0.

## 4. Invariants

1. ACTIVE only: reject VALIDATED, DECAYED, RETIRED, DISCOVERED.
2. No duplicates.
3. Stable ordering: sort EdgeIDs before hashing.
4. Deterministic PortfolioID from policy_id + sorted EdgeIDs.
5. Immutable membership: adding/removing edges creates a new PortfolioID.
6. No ProductionDecision in this stage.

## 5. Registry

PortfolioRegistry is built on the ADR-005 registry kernel.

Required helpers:

```text
register()
get()
history()
all_draft()
all_live()
```

## 6. AKB Integration

Portfolio writes graph facts:

```text
Portfolio node
Edge --ALLOCATED_TO--> Portfolio
```

## 7. Acceptance Criteria

- create portfolio from ACTIVE edges
- reject VALIDATED edge
- reject RETIRED/DECAYED edge
- reject duplicate edge
- deterministic id is order-insensitive
- immutable membership changes id
- equal weights generated and sum to 1.0
- PortfolioRegistry lookup works
- AKB allocation relationships created
- no ProductionDecision created
