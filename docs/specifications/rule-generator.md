# Specification: Rule Generator

Derived from: ADR-006 (Rule Grammar), ADR-005 (Registry Model)
Constitution: be37bf97... (Freeze v1.0, 2026-07-29)

Status: Draft (v0.1)

## 1. Purpose

RuleGenerator systematically produces candidate Rules from a parameter
grid. It is the "source of candidates" for Edge Discovery: feature
registry + operator + threshold grid → thousands of canonical Rules.

## 2. Input

A grid spec:

```python
{
    "RSI_14": {"<": [20, 25, 30, 35]},
    "ADX_14": {">": [20, 25, 30]},
}
```

- key = FeatureID
- operator ∈ {>, >=, <, <=, ==, !=} (Comparison ops, ADR-006 §2)
- thresholds = list of constants (P*/Z* thresholds are NOT generated
  in v0.1 — they need window context, out of scope)

## 3. Output

```text
tuple[Rule, ...]   # sorted by rule_id
```

Each Rule: `Rule(rule_id=..., ast=canonical_text, feature_ids=(FeatureID,))`.

## 4. Generation Rules

1. Each (FeatureID, operator, threshold) triple → one Comparison rule.
2. Canonical text via rules.canonical_text(parse(...)) — same identity
   as manual rules (dedup across sources).
3. Duplicates (identical canonical text) collapse to ONE Rule —
   the generator never emits the same rule_id twice.
4. Output sorted by rule_id (deterministic order).
5. Same grid + same constitution → identical output.

## 5. Invariants

1. Rule.rule_id == rules.rule_id(ast) — self-consistent identity.
2. rule.feature_ids == (FeatureID,) — declared features match rule body.
3. No duplicate rule_ids in output.
4. Empty grid → empty output (no error).

## 6. Acceptance Criteria

- single feature, multiple thresholds → N rules
- multiple features → combined rules, sorted by rule_id
- duplicate thresholds in grid → deduped (one rule)
- identical grid twice → identical output
- rule_id matches rules.rule_id(canonical_text)
- feature_ids populated
- empty grid → ()
