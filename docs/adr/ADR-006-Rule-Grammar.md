# ADR-006: Rule Grammar (AST)

- **Layer:** 1 (Domain & Contracts)
- **Status:** Ratified
- **Date:** 2026-07-29
- **Depends On:** ADR-005

## Context

Rules (and Feature formulas) must be machine-representable, optimizable, serializable, and hashable. String-based rules (`"RSI>P80 AND OI>P70"`) are ambiguous, unparseable across modules, and impossible to canonicalize. This ADR fixes the Abstract Syntax Tree (AST) as the single representation of all logical expressions in AlphaOS.

## Decision

### AST Supremacy

All Rules and Feature formulas are represented as an **AST**. String syntax exists only for human display and parsing INTO an AST; it is never the storage or execution format.

### Grammar

```text
Expression := Comparison | Logical | Unary
Comparison := FeatureRef OP Threshold      # OP ∈ {>, >=, <, <=, ==, !=}
Logical    := Expression AND Expression
            | Expression OR Expression
Unary      := NOT Expression
FeatureRef := FeatureID [ .transform ]     # transform ∈ {pct, z, raw, delta, …}
Threshold  := Constant | Percentile | ZScore
```

- Percentiles and z-scores are evaluated relative to a declared reference window at execution time (research) or from registry-stored anchors (production).
- N-ary operators are normalized to binary; canonical ordering is fixed (see Canonical Form).

### Canonical Form & Identity

1. ASTs are normalized: operators sorted, redundant `NOT` folded, constants simplified.
2. `RuleID = SHA256(canonical_ast_serialization)` — deterministic, content-addressed.
3. Identical rules across experiments share the same RuleID, enabling deduplication and cross-experiment statistics.

### Serialization

- Canonical text format for storage/hashing (specified in `docs/specifications/`).
- Execution backends compile the AST to native evaluators (numpy/polars) or SQL; the AST remains the source of truth.

## Consequences

- **Positive:** Deterministic identity; easy optimization, pruning, translation to SQL/vectorized code; explainability; deduplication.
- **Negative:** Writing a parser/compiler is required. Accepted — it is a one-time cost with permanent benefit.

## Alternatives Considered

- **String rules:** Rejected — ambiguous, unhashable, unsafe.
- **Python lambdas as rules:** Rejected — not serializable, not auditable, not deterministic across versions.

## Migration Path

None for v1.0.
