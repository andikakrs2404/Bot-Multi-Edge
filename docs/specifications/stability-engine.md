# Specification: Stability Engine

Derived from: ADR-000B (Trust Model), ADR-001 (Determinism)
Constitution: be37bf97... (Freeze v1.0, 2026-07-29)

Status: Draft (v0.1)

## 1. Purpose

StabilityEngine turns a WalkForwardResult into a formal verdict:
STABLE or UNSTABLE. Walk-forward produces numbers; stability produces
a decision — "can we trust this edge out-of-sample?"

## 2. Input

```python
WalkForwardResult
StabilityPolicy
```

## 3. StabilityPolicy

```python
@dataclass(frozen=True, slots=True)
class StabilityPolicy:
    policy_id: str
    min_stability: float      # default 0.75
    min_pass_ratio: float     # default 0.70 (passes / windows)
    min_oos_sharpe: float     # default 1.0
```

## 4. Verdict

```python
@dataclass(frozen=True, slots=True)
class StabilityVerdict:
    rule: str
    dataset_id: str
    verdict: str              # "STABLE" | "UNSTABLE"
    pass_ratio: float
    stability: float
    oos_sharpe_mean: float
    reasons: tuple[str, ...]  # failing checks, empty when STABLE
```

Edge is STABLE iff ALL of:

```text
stability    >= min_stability
pass_ratio   >= min_pass_ratio     (passes / n_windows)
oos_sharpe_mean >= min_oos_sharpe
```

Any check failing → UNSTABLE with the failing checks listed in
`reasons` (deterministic order: stability, pass_ratio, oos_sharpe).

## 5. Edge cases

- WalkForwardResult with zero windows cannot exist (validator rejects),
  but pass_ratio is still computed defensively as 0.0 if windows == 0.
- NaN inputs → fail the corresponding check (never silently pass).

## 6. Determinism

Same (result, policy) → same verdict. Pure function of inputs.

## 7. Acceptance criteria

- all thresholds met → STABLE, empty reasons
- stability below min → UNSTABLE, reason mentions "stability"
- pass ratio below min → UNSTABLE, reason mentions "pass_ratio"
- oos sharpe below min → UNSTABLE, reason mentions "oos_sharpe"
- multiple failures → multiple reasons, fixed order
- boundary: exactly at threshold → passes (>=, not >)
- deterministic twice
