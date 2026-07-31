"""Tests for AlphaOS Rule Grammar (ADR-006).

Spec: docs/specifications/rules.md
"""

import pytest

from shared.rules import (
    And,
    Comparison,
    FeatureValue,
    Not,
    Or,
    canonical_text,
    evaluate,
    matches,
    parse,
    rule_id,
    threshold_kind,
    threshold_value,
)


def ctx(**kw):
    return {k: FeatureValue(**v) for k, v in kw.items()}


class TestParser:
    def test_parse_comparison(self):
        ast = parse("(GT FEAT-RSI_14:PCT P80)")
        assert ast.to_text() == "(GT FEAT-RSI_14:PCT P80)"

    def test_parse_and_or_not(self):
        ast = parse("(AND (GT A P80) (OR (LT B Z1.5) (NOT (EQ C 0.5))))")
        assert isinstance(ast, And)
        assert isinstance(ast.right, Or)
        assert isinstance(ast.right.right, Not)

    def test_parse_rejects_garbage(self):
        with pytest.raises(ValueError):
            parse("(GT A)")
        with pytest.raises(ValueError):
            parse("AND A B")          # missing parens
        with pytest.raises(ValueError):
            parse("(GT A P80) extra")  # trailing tokens

    def test_roundtrip(self):
        text = "(AND (GT FEAT-A:PCT P80) (OR (LT FEAT-B:Z -1.5) (GT FEAT-C 0.05)))"
        assert parse(text).to_text() == text


class TestCanonicalForm:
    def test_commutative_normalization(self):
        a = "(AND (GT A P80) (GT B P70))"
        b = "(AND (GT B P70) (GT A P80))"
        assert canonical_text(parse(a)) == canonical_text(parse(b))

    def test_double_not_folded(self):
        assert canonical_text(parse("(NOT (NOT (GT A P80)))")) == "(GT A P80)"

    def test_rule_id_deterministic(self):
        assert rule_id("(GT A P80)") == rule_id("(GT A P80)")
        # semantically same rule via commutativity -> same id
        assert rule_id("(AND (GT A P80) (GT B P70))") == \
               rule_id("(AND (GT B P70) (GT A P80))")

    def test_rule_id_changes_with_threshold(self):
        assert rule_id("(GT A P80)") != rule_id("(GT A P90)")


class TestEvaluation:
    def test_percentile_comparison(self):
        r = "(GT FEAT-RSI_14:PCT P80)"
        assert matches(r, ctx(**{"FEAT-RSI_14": {"value": 70.0, "percentile": 90.0}}))
        assert not matches(r, ctx(**{"FEAT-RSI_14": {"value": 70.0, "percentile": 70.0}}))

    def test_zscore_comparison(self):
        r = "(GT FEAT-VOL:Z Z1.5)"
        assert matches(r, ctx(**{"FEAT-VOL": {"value": 1.0, "zscore": 2.0}}))
        assert not matches(r, ctx(**{"FEAT-VOL": {"value": 1.0, "zscore": 1.0}}))

    def test_constant_comparison(self):
        r = "(LT FEAT-ATR 0.05)"
        assert matches(r, ctx(**{"FEAT-ATR": {"value": 0.03}}))
        assert not matches(r, ctx(**{"FEAT-ATR": {"value": 0.07}}))

    def test_and_or_not_logic(self):
        r = "(AND (GT A P80) (NOT (LT B P20)))"
        assert matches(r, ctx(A={"value": 1, "percentile": 90}, B={"value": 1, "percentile": 50}))
        assert not matches(r, ctx(A={"value": 1, "percentile": 90}, B={"value": 1, "percentile": 10}))
        assert not matches(r, ctx(A={"value": 1, "percentile": 70}, B={"value": 1, "percentile": 50}))

    def test_or_satisfied_by_either(self):
        r = "(OR (GT A P90) (GT B P90))"
        assert matches(r, ctx(A={"value": 1, "percentile": 95}, B={"value": 1, "percentile": 50}))
        assert matches(r, ctx(A={"value": 1, "percentile": 50}, B={"value": 1, "percentile": 95}))

    def test_missing_feature_raises(self):
        with pytest.raises(KeyError):
            matches("(GT NOPE P80)", ctx(A={"value": 1, "percentile": 90}))

    def test_transform_is_informational(self):
        # threshold type selects the series, transform is metadata
        assert matches("(GT A:RAW P80)", ctx(A={"value": 1, "percentile": 90}))


class TestThresholds:
    def test_kinds(self):
        assert threshold_kind("P80") == "pct"
        assert threshold_kind("Z-1.5") == "z"
        assert threshold_kind("0.05") == "const"

    def test_values(self):
        assert threshold_value("P80") == 80.0
        assert threshold_value("Z1.5") == 1.5
        assert threshold_value("0.05") == 0.05

    def test_invalid_threshold(self):
        with pytest.raises(ValueError):
            threshold_kind("X80")
