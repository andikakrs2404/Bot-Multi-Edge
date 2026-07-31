"""AlphaOS Rule Grammar (ADR-006).

AST representation of Rules and Feature formulas. Spec:
docs/specifications/rules.md
"""

from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass
from typing import Protocol


# ── AST nodes ──

class Expr(Protocol):
    def to_text(self) -> str: ...


@dataclass(frozen=True, slots=True)
class Comparison:
    op: str                      # > >= < <= == !=
    feature: str                 # FeatureID, optional :transform
    threshold: str               # "P80" | "Z1.5" | "0.05"

    def to_text(self) -> str:
        return f"({self.op} {self.feature} {self.threshold})"


@dataclass(frozen=True, slots=True)
class And:
    left: Expr
    right: Expr

    def to_text(self) -> str:
        return f"(AND {self.left.to_text()} {self.right.to_text()})"


@dataclass(frozen=True, slots=True)
class Or:
    left: Expr
    right: Expr

    def to_text(self) -> str:
        return f"(OR {self.left.to_text()} {self.right.to_text()})"


@dataclass(frozen=True, slots=True)
class Not:
    expr: Expr

    def to_text(self) -> str:
        return f"(NOT {self.expr.to_text()})"


# ── threshold helpers ──

THRESHOLD_RE = re.compile(r"^(P(\d{1,3})|Z(-?\d+(?:\.\d+)?)|(-?\d+(?:\.\d+)?))$")


def threshold_kind(threshold: str) -> str:
    """'pct' | 'z' | 'const'"""
    m = THRESHOLD_RE.match(threshold)
    if not m:
        raise ValueError(f"invalid threshold: {threshold!r}")
    if m.group(2) is not None:
        return "pct"
    if m.group(3) is not None:
        return "z"
    return "const"


def threshold_value(threshold: str) -> float:
    m = THRESHOLD_RE.match(threshold)
    if not m:
        raise ValueError(f"invalid threshold: {threshold!r}")
    if m.group(2) is not None:
        return float(m.group(2))
    if m.group(3) is not None:
        return float(m.group(3))
    return float(m.group(4))


# ── parser (canonical text -> AST) ──

_TOKEN_RE = re.compile(r"\(|\)|[^\s()]+")


def parse(text: str) -> Expr:
    """Parse canonical text into an AST (ADR-006 §2)."""
    tokens = _TOKEN_RE.findall(text)
    pos = 0

    def peek() -> str:
        return tokens[pos] if pos < len(tokens) else ""

    def expect(tok: str) -> None:
        nonlocal pos
        if peek() != tok:
            raise ValueError(f"expected {tok!r}, got {peek()!r} at token {pos}")
        pos += 1

    def parse_expr() -> Expr:
        nonlocal pos
        if peek() != "(":
            raise ValueError(f"expected '(', got {peek()!r}")
        pos += 1  # consume '('
        head = peek()
        if head == "AND":
            pos += 1
            left, right = parse_expr(), parse_expr()
            expect(")")
            return And(left, right)
        if head == "OR":
            pos += 1
            left, right = parse_expr(), parse_expr()
            expect(")")
            return Or(left, right)
        if head == "NOT":
            pos += 1
            inner = parse_expr()
            expect(")")
            return Not(inner)
        if head in ("GT", "GTE", "LT", "LTE", "EQ", "NEQ"):
            pos += 1
            feature = peek()
            if not feature or feature == "(":
                raise ValueError(f"expected FeatureRef, got {feature!r}")
            pos += 1
            threshold = peek()
            if not threshold or threshold == "(":
                raise ValueError(f"expected Threshold, got {threshold!r}")
            pos += 1
            expect(")")
            return Comparison(head, feature, threshold)
        raise ValueError(f"unknown node {head!r}")

    ast = parse_expr()
    if pos != len(tokens):
        raise ValueError(f"trailing tokens at {pos}: {tokens[pos:]}")
    return ast


# ── canonicalization (ADR-006 §3) ──

def canonicalize(expr: Expr) -> Expr:
    """Normalize: sort AND/OR operands, fold double NOT."""
    if isinstance(expr, Comparison):
        return expr
    if isinstance(expr, Not):
        inner = canonicalize(expr.expr)
        if isinstance(inner, Not):
            return inner.expr  # fold NOT NOT
        return Not(inner)
    if isinstance(expr, (And, Or)):
        left = canonicalize(expr.left)
        right = canonicalize(expr.right)
        if left.to_text() > right.to_text():
            left, right = right, left  # commutative normalization
        cls = And if isinstance(expr, And) else Or
        return cls(left, right)
    raise TypeError(f"unknown expr {expr!r}")


def canonical_text(expr: Expr) -> str:
    return canonicalize(expr).to_text()


def rule_id(text: str) -> str:
    """RuleID = SHA256(canonical text) (ADR-006 §4)."""
    canonical = canonical_text(parse(text))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ── evaluation (ADR-006 §5) ──

@dataclass(frozen=True, slots=True)
class FeatureValue:
    value: float
    percentile: float = math.nan   # 0..100
    zscore: float = math.nan


FeatureContext = dict[str, FeatureValue]


def _series(v: FeatureValue, kind: str) -> float:
    if kind == "pct":
        return v.percentile
    if kind == "z":
        return v.zscore
    return v.value


_OP_MAP = {"GT": ">", "GTE": ">=", "LT": "<", "LTE": "<=", "EQ": "==", "NEQ": "!="}


def _compare(op: str, a: float, b: float) -> bool:
    op = _OP_MAP.get(op, op)
    if op == ">":
        return a > b
    if op == ">=":
        return a >= b
    if op == "<":
        return a < b
    if op == "<=":
        return a <= b
    if op == "==":
        return a == b
    if op == "!=":
        return a != b
    raise ValueError(f"unknown op {op!r}")


def evaluate(expr: Expr, ctx: FeatureContext) -> bool:
    """Evaluate AST against a feature context (ADR-006 §5)."""
    if isinstance(expr, Comparison):
        name, _, transform = expr.feature.partition(":")
        try:
            fv = ctx[name]
        except KeyError:
            raise KeyError(f"feature {name!r} missing from context") from None
        kind = threshold_kind(expr.threshold)
        series = _series(fv, kind)
        return _compare(expr.op, series, threshold_value(expr.threshold))
    if isinstance(expr, And):
        return evaluate(expr.left, ctx) and evaluate(expr.right, ctx)
    if isinstance(expr, Or):
        return evaluate(expr.left, ctx) or evaluate(expr.right, ctx)
    if isinstance(expr, Not):
        return not evaluate(expr.expr, ctx)
    raise TypeError(f"unknown expr {expr!r}")


def matches(text: str, ctx: FeatureContext) -> bool:
    """Convenience: parse canonical text and evaluate."""
    return evaluate(parse(text), ctx)
