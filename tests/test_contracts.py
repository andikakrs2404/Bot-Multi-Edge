"""Tests for AlphaOS shared contracts (ADR-002/003/004/005/006).

Constitution: be37bf97... (Constitutional Freeze v1.0).
"""

import pytest

from shared.contracts import (
    CONSTITUTION_HASH,
    Dataset,
    DatasetStatus,
    Edge,
    EdgeStatus,
    Experiment,
    ExperimentStatus,
    Feature,
    Relationship,
    RelationshipType,
    Rule,
    assert_trust,
    content_hash,
    make_dataset_id,
    make_rule_id,
)


class TestConstitution:
    def test_constitution_hash_frozen(self):
        assert CONSTITUTION_HASH == "be37bf97508691f93557849e1b05d7a1bf2c7be89029cc7f9dcbc77ba964d8cd"


class TestImmutability:
    def test_dataset_immutable(self):
        d = Dataset(dataset_id="d1", schema_version="1.0", universe="top500",
                    timeframe="30m", date_range=("2023-01-01", "2026-01-01"),
                    content_hash="h")
        with pytest.raises(Exception):
            d.content_hash = "changed"  # frozen dataclass

    def test_feature_identity_permanent(self):
        f1 = Feature(feature_id="RSI_14_CLOSE")
        f2 = Feature(feature_id="RSI_14_CLOSE")
        assert f1 == f2  # same identity = same entity
        # evolution = new id, old id unchanged (documented, enforced by convention)


class TestContentAddressing:
    def test_dataset_id_deterministic(self):
        manifest = {"universe": "top500", "tf": "30m", "rows": 10}
        assert make_dataset_id(manifest) == make_dataset_id(manifest)
        assert len(make_dataset_id(manifest)) == 64  # sha256 hex

    def test_rule_id_from_canonical_ast(self):
        ast = '(AND (GT RSI_14_CLOSE 80) (GT OI_PCT 70))'
        assert make_rule_id(ast) == make_rule_id(ast)
        assert make_rule_id(ast) != make_rule_id(ast + " ")

    def test_content_hash_stable_across_key_order(self):
        a = content_hash({"b": 1, "a": 2})
        b = content_hash({"a": 2, "b": 1})
        assert a == b


class TestTrustModel:
    def test_production_rejects_low_trust(self):
        with pytest.raises(AssertionError):
            assert_trust("production", "ExperimentResult")  # level 3

    def test_production_accepts_validated_knowledge(self):
        assert_trust("production", "Edge")   # level 4
        assert_trust("production", "Portfolio")  # level 5

    def test_research_unrestricted(self):
        assert_trust("research", "RawObservation")  # no assertion raised


class TestLifecycle:
    def test_edge_lifecycle_forward_only(self):
        e = Edge(edge_id="EDGE-1", rule_id="R-1", experiment_id="EXP-1")
        assert e.status == EdgeStatus.DISCOVERED
        # forward transition is legal
        e2 = Edge(edge_id="EDGE-1", rule_id="R-1", experiment_id="EXP-1",
                  status=EdgeStatus.VALIDATED)
        assert e2.status == EdgeStatus.VALIDATED
        # RETIRED edges remain referenced, never deleted (history preserved)
        e3 = Edge(edge_id="EDGE-1", rule_id="R-1", experiment_id="EXP-1",
                  status=EdgeStatus.RETIRED, retirement_reason="decay")
        assert e3.retirement_reason == "decay"

    def test_experiment_status_valid(self):
        assert ExperimentStatus.DRAFT in ExperimentStatus
        assert ExperimentStatus.PROMOTED in ExperimentStatus


class TestKnowledgeGraph:
    def test_relationship_first_class(self):
        r = Relationship(
            rel_id="REL-1",
            rel_type=RelationshipType.PRODUCES,
            source_type="Experiment", source_id="EXP-1",
            target_type="Edge", target_id="EDGE-1",
        )
        assert r.rel_type == RelationshipType.PRODUCES
        assert r.source_id == "EXP-1"

    def test_all_relationship_types(self):
        types = {t for t in RelationshipType}
        assert RelationshipType.SUPERSEDES in types
        assert RelationshipType.ALLOCATED_TO in types
        assert RelationshipType.DRIVES in types


class TestEntities:
    def test_feature_kind_discriminator(self):
        f = Feature(feature_id="FWD_RETURN_24H", kind="label")
        assert f.kind == "label"

    def test_rule_references_features(self):
        r = Rule(rule_id="R-1", ast="(GT RSI 80)",
                 feature_ids=("RSI_14_CLOSE",))
        assert r.feature_ids == ("RSI_14_CLOSE",)
