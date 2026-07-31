# Specification: Activation Engine

Derived from: ADR-002A (Edge Lifecycle), ADR-009 (AKB)
Constitution: be37bf97... (Freeze v1.0, 2026-07-29)

Status: Draft (v0.1)

## 1. Purpose

The Activation Engine is the formal gatekeeper between the Research and
Production realms. It answers the question: "Of all validated knowledge,
which is trusted for production use?"

It consumes `Edge(VALIDATED)` and promotes it to `Edge(ACTIVE)`.

It does NOT manage portfolios or make trading decisions.

## 2. ActivationPolicy

Activation is governed by an explicit, immutable, and traceable policy,
not hardcoded logic.

```python
@dataclass(frozen=True)
class ActivationPolicy:
    policy_id: str
    min_sharpe: float
    min_profit_factor: float
    max_evidence_age_days: int
    min_sample: int
```

## 3. ActivationRecord

Promotion is not a silent status change. It produces an auditable
`ActivationRecord` in the AKB.

```python
@dataclass(frozen=True)
class ActivationRecord:
    activation_id: str
    edge_id: str
    policy_id: str
    activated_at: datetime
    reason: str
```

This answers "Why did EDGE-123 become ACTIVE?". A similar record is
created for decay.

## 4. Edge Lifecycle Transitions

The Activation Engine is responsible for two key transitions:

1.  `VALIDATED` → `ACTIVE`: When a validated edge meets the activation policy.
2.  `ACTIVE` → `DECAYED`: When an active edge no longer meets freshness criteria (e.g., its supporting evidence is too old).

The engine does NOT handle:

-   `DECAYED` → `ACTIVE` (requires re-validation, which is a new Experiment/Evidence cycle)
-   `ACTIVE` → `RETIRED` (manual governance decision)

## 5. AKB Integration

The engine writes graph facts:

-   `ActivationRecord` node
-   `Edge` status update (`VALIDATED` → `ACTIVE`)
-   Relationships: `Edge --ACTIVATED_BY--> ActivationRecord`, `ActivationRecord --USES--> ActivationPolicy`

## 6. Acceptance Criteria

-   `Edge(VALIDATED)` can be promoted to `Edge(ACTIVE)` if it meets policy.
-   Edges not meeting policy are not promoted.
-   `Edge(ACTIVE)` can be marked `Edge(DECAYED)` if its evidence is too old.
-   Promotion and decay create auditable records.
-   `ActivationPolicy` is enforced.
-   Lifecycle transitions are managed via `EdgeRegistry.set_status()`.
-   AKB relationships are created.
