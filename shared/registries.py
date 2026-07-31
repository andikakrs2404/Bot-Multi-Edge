"""Concrete AlphaOS registries (ADR-005, spec §8).

FeatureRegistry (kind feature|label), RuleRegistry, DatasetRegistry,
EdgeRegistry — all built on the generic Registry kernel.
"""

from __future__ import annotations

from .contracts import Dataset, Edge, Feature, Rule
from .registry import Registry


class FeatureRegistry(Registry[Feature]):
    """Feature + Label registry (same kernel, kind discriminator)."""

    kind = "feature_or_label"
    identity_prefix = "FEAT-"

    def _identity_of(self, entity: Feature) -> str:
        return entity.feature_id


class RuleRegistry(Registry[Rule]):
    """Rule registry — identity is the content-addressed RuleID."""

    kind = "rule"
    identity_prefix = "RULE-"

    def _identity_of(self, entity: Rule) -> str:
        return entity.rule_id


class DatasetRegistry(Registry[Dataset]):
    """Dataset registry — identity is the content hash."""

    kind = "dataset"
    identity_prefix = "DS-"

    def _identity_of(self, entity: Dataset) -> str:
        return entity.dataset_id


class EdgeRegistry(Registry[Edge]):
    """Edge registry — living entities with lifecycle."""

    kind = "edge"
    identity_prefix = "EDGE-"

    def _identity_of(self, entity: Edge) -> str:
        return entity.edge_id
