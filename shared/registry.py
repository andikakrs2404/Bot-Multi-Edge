"""AlphaOS Registry Kernel (ADR-005).

Source of truth for domain entity definitions. No entity may be used by
an Experiment before registration. Spec: docs/specifications/registry.md.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Generic, TypeVar

from .contracts import CONSTITUTION_HASH, utcnow

T = TypeVar("T")


class RegistryStatus(str, Enum):
    REGISTERED = "REGISTERED"
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    ARCHIVED = "ARCHIVED"


@dataclass(frozen=True, slots=True)
class RegistryEntry(Generic[T]):
    """One registry entry (spec §2)."""
    entity_id: str
    entity: T
    version: int = 1
    status: RegistryStatus = RegistryStatus.REGISTERED
    created_at: datetime = field(default_factory=utcnow)
    created_by: str = "system"
    superseded_by: str | None = None
    constitution_hash: str = CONSTITUTION_HASH
    registry_version: int = 0  # global per-registry counter at entry time


class DuplicateActiveError(ValueError):
    """Registering a second ACTIVE entry for an already-ACTIVE identity."""


class UnknownIdentityError(KeyError):
    """No entry exists for the given entity_id."""


class Registry(Generic[T]):
    """Generic registry kernel (ADR-005, spec §3-§6).

    Immutable entries; one ACTIVE per identity; supersession via
    supersede(); global registry_version bumped on every mutation.
    """

    kind: str = "generic"
    identity_prefix: str = "ID"

    def __init__(self) -> None:
        self._entries: dict[str, list[RegistryEntry[T]]] = {}
        self._registry_version = 0

    # ── queries (spec §6) ──

    def get(self, entity_id: str) -> T:
        """ACTIVE entry for the identity."""
        return self.latest_entry(entity_id).entity

    def latest_entry(self, entity_id: str) -> RegistryEntry[T]:
        try:
            versions = self._entries[entity_id]
        except KeyError:
            raise UnknownIdentityError(entity_id) from None
        for e in reversed(versions):
            if e.status == RegistryStatus.ACTIVE:
                return e
        # no ACTIVE: return the most recent entry (archived/superseded)
        return versions[-1]

    def get_version(self, entity_id: str, version: int) -> RegistryEntry[T]:
        try:
            versions = self._entries[entity_id]
        except KeyError:
            raise UnknownIdentityError(entity_id) from None
        for e in versions:
            if e.version == version:
                return e
        raise KeyError(f"{entity_id} has no version {version}")

    def history(self, entity_id: str) -> list[RegistryEntry[T]]:
        try:
            return list(self._entries[entity_id])
        except KeyError:
            raise UnknownIdentityError(entity_id) from None

    def all_active(self) -> list[RegistryEntry[T]]:
        out = []
        for versions in self._entries.values():
            for e in versions:
                if e.status == RegistryStatus.ACTIVE:
                    out.append(e)
        return out

    def registry_version(self) -> int:
        return self._registry_version

    # ── mutations (spec §4, §5) ──

    def register(self, entity: T, created_by: str = "system") -> RegistryEntry[T]:
        """Register a new entry. Fails on duplicate ACTIVE identity."""
        entity_id = self._identity_of(entity)
        self._bump()
        if entity_id in self._entries:
            versions = self._entries[entity_id]
            if versions[-1].status in (RegistryStatus.ACTIVE, RegistryStatus.REGISTERED):
                raise DuplicateActiveError(
                    f"{entity_id} already {versions[-1].status}; supersede first"
                )
            version = versions[-1].version + 1
        else:
            version = 1
        entry = RegistryEntry(
            entity_id=entity_id,
            entity=entity,
            version=version,
            status=RegistryStatus.ACTIVE,
            created_by=created_by,
            registry_version=self._registry_version,
        )
        self._entries.setdefault(entity_id, []).append(entry)
        return entry

    def supersede(self, entity_id: str, successor_id: str,
                  created_by: str = "system") -> RegistryEntry[T]:
        """Mark ACTIVE entry SUPERSEDED, pointing to successor (spec §5)."""
        entry = self.latest_entry(entity_id)
        if entry.status != RegistryStatus.ACTIVE:
            raise ValueError(f"{entity_id} not ACTIVE; cannot supersede")
        self._bump()
        replaced = RegistryEntry(
            entity_id=entry.entity_id,
            entity=entry.entity,
            version=entry.version,
            status=RegistryStatus.SUPERSEDED,
            created_at=entry.created_at,
            created_by=entry.created_by,
            superseded_by=successor_id,
            constitution_hash=entry.constitution_hash,
            registry_version=entry.registry_version,
        )
        versions = self._entries[entity_id]
        versions[-1] = replaced
        return replaced

    def archive(self, entity_id: str, created_by: str = "system") -> RegistryEntry[T]:
        """Move ACTIVE entry to ARCHIVED (retired, not superseded)."""
        entry = self.latest_entry(entity_id)
        if entry.status != RegistryStatus.ACTIVE:
            raise ValueError(f"{entity_id} not ACTIVE; cannot archive")
        self._bump()
        archived = RegistryEntry(
            entity_id=entry.entity_id,
            entity=entry.entity,
            version=entry.version,
            status=RegistryStatus.ARCHIVED,
            created_at=entry.created_at,
            created_by=entry.created_by,
            superseded_by=None,
            constitution_hash=entry.constitution_hash,
            registry_version=entry.registry_version,
        )
        versions = self._entries[entity_id]
        versions[-1] = archived
        return archived

    # ── validation (spec §7) ──

    def validate(self, entry: RegistryEntry[T]) -> list[str]:
        """Return list of violations; empty list = valid."""
        violations = []
        if entry.constitution_hash != CONSTITUTION_HASH:
            violations.append("constitution_hash mismatch")
        if not entry.entity_id or not entry.entity_id.startswith(self.identity_prefix):
            violations.append(f"entity_id must start with {self.identity_prefix}")
        return violations

    # ── helpers ──

    def _identity_of(self, entity: T) -> str:
        raise NotImplementedError

    def _bump(self) -> None:
        self._registry_version += 1
