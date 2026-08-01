"""Tests for AlphaOS RuleGenerator (grid → canonical Rules)."""

import pytest

from shared.contracts import Rule
from shared.rules import parse
from shared.rule_generator import generate


class TestSingleFeature:
    def test_multiple_thresholds(self):
        rules = generate({"RSI_14": {"<": [20, 25, 30]}})

        assert len(rules) == 3
        assert all(isinstance(r, Rule) for r in rules)
        texts = sorted(r.ast for r in rules)
        assert texts == [
            "(LT RSI_14 20)",
            "(LT RSI_14 25)",
            "(LT RSI_14 30)",
        ]

    def test_ast_is_canonical(self):
        rules = generate({"RSI_14": {">": [30]}})
        # canonical_text(parse(x)) == x for already-canonical text
        assert rules[0].ast == "(GT RSI_14 30)"


class TestMultipleFeatures:
    def test_combined_sorted_by_rule_id(self):
        rules = generate({
            "RSI_14": {"<": [30]},
            "ADX_14": {">": [20, 25]},
        })

        assert len(rules) == 3
        ids = [r.rule_id for r in rules]
        assert ids == sorted(ids)
        assert len(set(ids)) == 3


class TestDeduplication:
    def test_duplicate_thresholds_collapse(self):
        rules = generate({"RSI_14": {"<": [20, 20, 20]}})

        assert len(rules) == 1

    def test_rule_id_matches_canonical(self):
        rules = generate({"RSI_14": {"<": [20]}})
        from shared.rules import rule_id as canonical_rule_id

        assert rules[0].rule_id == canonical_rule_id("(LT RSI_14 20)")


class TestDeterminism:
    def test_identical_grid_identical_output(self):
        grid = {"RSI_14": {"<": [20, 30]}, "ADX_14": {">": [25]}}
        a = generate(grid)
        b = generate(grid)

        assert a == b
        assert [r.rule_id for r in a] == [r.rule_id for r in b]


class TestFeatureIds:
    def test_feature_ids_populated(self):
        rules = generate({"RSI_14": {"<": [20]}})

        assert rules[0].feature_ids == ("RSI_14",)

    def test_multiple_features_each_has_own(self):
        rules = generate({
            "RSI_14": {"<": [20]},
            "ADX_14": {">": [25]},
        })
        by_ast = {r.ast: r for r in rules}

        assert by_ast["(LT RSI_14 20)"].feature_ids == ("RSI_14",)
        assert by_ast["(GT ADX_14 25)"].feature_ids == ("ADX_14",)


class TestEmpty:
    def test_empty_grid_empty_output(self):
        assert generate({}) == ()
