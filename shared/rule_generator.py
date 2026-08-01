"""AlphaOS RuleGenerator: parameter grid → canonical candidate Rules.

Systematic source of Rule candidates for Edge Discovery (ADR-006).
Grid: {FeatureID: {operator: [thresholds]}} → sorted tuple[Rule, ...].
"""

from __future__ import annotations

from .contracts import Rule
from .rules import canonical_text, parse, rule_id

_OPS = {">": "GT", ">=": "GTE", "<": "LT", "<=": "LTE", "==": "EQ", "!=": "NEQ"}


def generate(grid: dict[str, dict[str, list[float]]]) -> tuple[Rule, ...]:
    """Generate canonical Rules from a threshold grid.

    Deterministic: output sorted by rule_id, duplicates collapsed.
    """
    seen: dict[str, Rule] = {}
    for feature_id in sorted(grid):
        for op in sorted(grid[feature_id]):
            if op not in _OPS:
                raise ValueError(f"unknown operator {op!r}")
            token = _OPS[op]
            for threshold in sorted(grid[feature_id][op]):
                text = f"({token} {feature_id} {threshold:g})"
                ast = canonical_text(parse(text))
                rid = rule_id(ast)
                seen[rid] = Rule(rule_id=rid, ast=ast,
                                 feature_ids=(feature_id,))
    return tuple(seen[r] for r in sorted(seen))
