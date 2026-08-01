# Specification: Edge Promotion Policy

Derived from: ADR-002A (Lifecycles), ADR-000B (Trust Model), ADR-001
(Determinism)
Constitution: be37bf97... (Freeze v1.0, 2026-07-29)

Status: Draft (v0.1)

## 1. Purpose

PromotionEngine is the formal gate between Research and Production
domains. It combines every validation signal into one objective
verdict: PROMOTABLE or NON_PROMOTABLE.

Before: VALIDATED meant "passed the validator once".
Now: PROMOTABLE means "cleared walk-forward, stability, regime, and
rank gates — eligible for Production consumption".

## 2. Inputs

```text
Edge              (status)
RankedEdge        (score)
StabilityVerdict  (verdict STABLE/UNSTABLE)
RegimeResult      (robustness)
PromotionPolicy
```

## 3. PromotionPolicy

```python
@dataclass(frozen=True, slots=True)
class PromotionPolicy:
    policy_id: str
    min_rank_score: float
    min_stability: float
    min_regime_robustness: float
    require_validated: bool = True
```

## 4. Rules (v1)

PROMOTABLE iff ALL:

```text
status == VALIDATED              (if require_validated)
rank_score  >= min_rank_score
stability   >= min_stability
robustness  >= min_regime_robustness
```

Failure reasons (deterministic order):

```text
("not_validated", "rank_score_below_threshold", "unstable",
 "regime_not_robust")
```

`reasons` lists only the failing checks; empty when PROMOTABLE.

Note: stability verdict is derived from StabilityEngine — an edge with
`UNSTABLE` verdict has stability < policy minimum, so both checks are
covered by the numeric `min_stability` gate. The verdict enum is kept
for explainability; the engine compares numbers.

## 5. PromotionResult

```python
@dataclass(frozen=True, slots=True)
class PromotionResult:
    edge_id: str
    verdict: PromotionVerdict   # PROMOTABLE | NON_PROMOTABLE
    reasons: tuple[str, ...]
```

## 6. Edge cases (fail-closed)

- NaN in any numeric input → that check fails.
- Missing input signal (None) → fails its check.

## 7. Determinism

Same inputs → same verdict + reasons. Pure function.

## 8. Acceptance criteria

- all gates met → PROMOTABLE, empty reasons
- status not VALIDATED (require_validated) → NON_PROMOTABLE
  reason "not_validated"
- rank below min → reason "rank_score_below_threshold"
- stability below min → reason "unstable"
- robustness below min → reason "regime_not_robust"
- multiple failures → multiple reasons, fixed order
- boundary: exactly at threshold → passes (>=)
- NaN → fails
- deterministic twice
