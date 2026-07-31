"""Concrete AlphaOS registries (ADR-005, spec §8).

FeatureRegistry (kind feature|label), RuleRegistry, DatasetRegistry,
EdgeRegistry — all built on the generic Registry kernel.
"""

from __future__ import annotations

from dataclasses import replace

from .contracts import Dataset, Edge, EdgeStatus, Feature, Rule
from .registry import Registry, RegistryEntry


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

    def all_validated(self) -> list[RegistryEntry[Edge]]:
        return [e for e in super().all_active() if e.entity.status == EdgeStatus.VALIDATED]

    def all_active(self) -> list[RegistryEntry[Edge]]:
        return [e for e in super().all_active() if e.entity.status == EdgeStatus.ACTIVE]

    def all_decayed(self) -> list[RegistryEntry[Edge]]:
        return [e for e in super().all_active() if e.entity.status == EdgeStatus.DECAYED]

    def set_status(self, entry: RegistryEntry[Edge], status: EdgeStatus) -> RegistryEntry[Edge]:
        """Advance Edge lifecycle in place (Portfolio/monitoring stages use this)."""
        return self.replace_entry(entry, replace(entry.entity, status=status))


class PortfolioRegistry(Registry):
    """Portfolio registry — immutable ACTIVE-edge selections."""

    kind = "portfolio"
    identity_prefix = "PORT-"

    def _identity_of(self, entity) -> str:
        return entity.portfolio_id

    def all_draft(self):
        from .contracts import PortfolioStatus
        return [e for e in super().all_active() if e.entity.status == PortfolioStatus.DRAFT]

    def all_live(self):
        from .contracts import PortfolioStatus
        return [e for e in super().all_active() if e.entity.status == PortfolioStatus.LIVE]
