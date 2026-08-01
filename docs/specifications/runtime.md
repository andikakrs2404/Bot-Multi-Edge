# Specification: Runtime Artifacts (MarketSnapshot)

Derived from: ADR-003 (Data Contract), ADR-002 (Domain Ontology separation)
Constitution: be37bf97... (Freeze v1.0, 2026-07-29)

Status: Draft (v0.1)

## 1. Purpose

Runtime artifacts represent point-in-time observations of live market
state. They are NOT domain objects and do NOT live in `shared/contracts.py`.

Domain objects (Dataset, Feature, Rule, Edge, Portfolio, DecisionSignal)
have lifecycle and knowledge value. Runtime artifacts are ephemeral
inputs consumed by the Signal/Decision layer and then discarded.

## 2. Separation rule

- `shared/contracts.py` = domain ontology (ADR-002), immutable, constitutional.
- `shared/runtime.py` = runtime evaluation artifacts, versioned separately.

## 3. MarketSnapshot

```python
@dataclass(frozen=True, slots=True)
class MarketSnapshot:
    snapshot_id: str
    symbol: str
    timestamp: datetime
    feature_values: dict[str, float]
```

- `snapshot_id`: deterministic content hash over (symbol, timestamp,
  sorted feature_values) — identical observations produce identical ids
  (ADR-001 deterministic production).
- `feature_values`: feature_id -> value, pre-normalized, NaN-free.
- Timestamp must be timezone-aware (UTC).

## 4. Invariants

1. `feature_values` must not be empty.
2. No NaN/inf values.
3. Timestamp must be timezone-aware.
4. `snapshot_id` deterministic: same inputs -> same id.

## 5. Acceptance Criteria

- create MarketSnapshot with feature values
- snapshot_id deterministic (order-insensitive feature_values)
- snapshot_id changes when feature values change
- empty feature_values rejected
- NaN rejected
- naive timestamp rejected
