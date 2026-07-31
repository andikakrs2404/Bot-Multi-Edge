# Specification: Rule Grammar (AST)

Derived from: ADR-006 (Rule Grammar), ADR-002 (Domain Ontology)
Constitution: be37bf97... (Freeze v1.0, 2026-07-29)

Status: Draft (v0.1)

## 1. Representation

All Rules and Feature formulas are **Abstract Syntax Trees (AST)**. Strings exist only for display, parsing, and hashing — never as storage or execution format (ADR-006).

## 2. Node Types

```text
Expression := Comparison | And | Or | Not
Comparison := ( OP FeatureRef Threshold )     OP ∈ { >, >=, <, <=, ==, != }
And        := ( AND Expression Expression )
Or         := ( OR  Expression Expression )
Not        := ( NOT Expression )
FeatureRef := FeatureID [ ":" transform ]     transform ∈ { pct, z, raw, delta }
Threshold  := P<int>                          # percentile 0..100
            | Z<float>                        # z-score
            | <float>                         # constant
```

## 3. Canonical Form

1. `AND` / `OR` operands are sorted by their canonical serialization (commutativity normalization).
2. Double negation `NOT NOT X` folds to `X`.
3. Canonical text is the single serialization used for hashing and identity.

### Canonical Text Format

```text
(GT FEAT-RSI_14:PCT P80)
(AND (GT FEAT-RSI_14:PCT P80) (GT FEAT-OI_1H:Z 1.5))
(NOT (LT FEAT-ATR_PCT:PCT P20))
```

## 4. Identity

```text
RuleID = SHA256( canonical_text )
```

- Identical rules ⇒ identical RuleID (deduplication across experiments).
- RuleID is the identity used by RuleRegistry (ADR-005).

## 5. Evaluation

`evaluate(expr, ctx)` where `ctx[FeatureID] = (value, percentile, zscore)`:

| Threshold | Series compared |
| --- | --- |
| `P<n>` | percentile (0..100) |
| `Z<n>` | zscore |
| constant | raw value |

`FeatureRef.transform` is informational (declares which series is meaningful); the threshold type selects the series at evaluation.

## 6. Registration Requirement

A Rule MUST be registered in RuleRegistry before any Experiment references it (ADR-005). Unregistered rules are forbidden in experiments.
