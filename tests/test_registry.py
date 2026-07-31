"""Tests for AlphaOS Registry Kernel (ADR-005).

Spec: docs/specifications/registry.md
Constitution: be37bf97... (Freeze v1.0).
"""

import pytest

from shared.contracts import Dataset, Edge, Experiment, Feature, Rule
from shared.registries import DatasetRegistry, EdgeRegistry, FeatureRegistry, RuleRegistry
from shared.registry import DuplicateActiveError, RegistryStatus, UnknownIdentityError


def make_feature(fid: str, kind: str = "feature") -> Feature:
    return Feature(feature_id=fid, kind=kind, category="momentum", formula=f"(def {fid})")


def make_rule(rid: str) -> Rule:
    return Rule(rule_id=rid, ast=f"(GT {rid} 80)", feature_ids=("F",))


def make_dataset(did: str) -> Dataset:
    return Dataset(dataset_id=did, schema_version="1.0", universe="top500",
                   timeframe="30m", date_range=("2023", "2026"), content_hash="h")


def make_edge(eid: str) -> Edge:
    return Edge(edge_id=eid, rule_id="RULE-1", experiment_id="EXP-1")


class TestRegistryKernel:
    def test_register_and_get(self):
        r = FeatureRegistry()
        r.register(make_feature("FEAT-RSI_14"))
        f = r.get("FEAT-RSI_14")
        assert f.feature_id == "FEAT-RSI_14"

    def test_registry_version_increments(self):
        r = FeatureRegistry()
        assert r.registry_version() == 0
        r.register(make_feature("FEAT-A"))
        assert r.registry_version() == 1
        r.register(make_feature("FEAT-B"))
        assert r.registry_version() == 2

    def test_entry_records_registry_version(self):
        r = FeatureRegistry()
        e1 = r.register(make_feature("FEAT-A"))
        r.register(make_feature("FEAT-B"))
        e2 = r.register(make_feature("FEAT-C"))
        assert e1.registry_version == 1
        assert e2.registry_version == 3

    def test_constitution_hash_recorded(self):
        r = FeatureRegistry()
        e = r.register(make_feature("FEAT-A"))
        assert e.constitution_hash == "be37bf97508691f93557849e1b05d7a1bf2c7be89029cc7f9dcbc77ba964d8cd"

    def test_duplicate_active_rejected(self):
        r = FeatureRegistry()
        r.register(make_feature("FEAT-A"))
        with pytest.raises(DuplicateActiveError):
            r.register(make_feature("FEAT-A"))

    def test_unknown_identity(self):
        r = FeatureRegistry()
        with pytest.raises(UnknownIdentityError):
            r.get("FEAT-NOPE")

    def test_register_after_archive_allowed(self):
        r = FeatureRegistry()
        r.register(make_feature("FEAT-A"))
        r.archive("FEAT-A")
        e = r.register(make_feature("FEAT-A"))  # new lifecycle version
        assert e.version == 2
        assert e.status == RegistryStatus.ACTIVE


class TestSupersession:
    def test_supersede_marks_and_points(self):
        r = FeatureRegistry()
        r.register(make_feature("FEAT-OLD"))
        r.register(make_feature("FEAT-NEW"))
        r.supersede("FEAT-OLD", "FEAT-NEW")
        old = r.history("FEAT-OLD")[-1]
        assert old.status == RegistryStatus.SUPERSEDED
        assert old.superseded_by == "FEAT-NEW"

    def test_supersede_requires_active(self):
        r = FeatureRegistry()
        r.register(make_feature("FEAT-A"))
        r.archive("FEAT-A")
        with pytest.raises(ValueError):
            r.supersede("FEAT-A", "FEAT-B")

    def test_history_preserved(self):
        r = FeatureRegistry()
        r.register(make_feature("FEAT-A"))
        r.archive("FEAT-A")
        r.register(make_feature("FEAT-A"))
        hist = r.history("FEAT-A")
        assert [h.status for h in hist] == [RegistryStatus.ARCHIVED, RegistryStatus.ACTIVE]
        assert [h.version for h in hist] == [1, 2]


class TestConcreteRegistries:
    def test_feature_kind_discriminator(self):
        r = FeatureRegistry()
        r.register(make_feature("FEAT-RSI", kind="feature"))
        r.register(make_feature("LAB-FWD_RETURN", kind="label"))
        kinds = {e.entity.kind for e in r.all_active()}
        assert kinds == {"feature", "label"}

    def test_rule_identity_content_addressed(self):
        r = RuleRegistry()
        r.register(make_rule("RULE-abc"))
        with pytest.raises(DuplicateActiveError):
            r.register(make_rule("RULE-abc"))  # same id = same rule

    def test_dataset_registry(self):
        r = DatasetRegistry()
        r.register(make_dataset("DS-1"))
        assert r.get("DS-1").timeframe == "30m"

    def test_edge_registry_lifecycle(self):
        r = EdgeRegistry()
        e = r.register(make_edge("EDGE-1"))
        assert e.entity.status.value == "DISCOVERED"  # EdgeStatus from contracts

    def test_validation_requires_prefix(self):
        r = FeatureRegistry()
        e = r.register(make_feature("BAD_ID"))  # no FEAT- prefix
        violations = r.validate(e)
        assert any("entity_id must start with" in v for v in violations)
