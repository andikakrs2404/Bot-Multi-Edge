"""AlphaOS Evidence Model (ADR-008, spec evidence-model).

Evidence = immutable record binding metrics + artifacts to a Candidate,
with a reviewable lifecycle. Registry-backed (ADR-005 kernel).
Edge promotion happens in the Validator stage, not here.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .contracts import CONSTITUTION_HASH, utcnow
from .registry import Registry, RegistryEntry, RegistryStatus


class EvidenceStatus(str, Enum):
    GENERATED = "GENERATED"
    REVIEWED = "REVIEWED"
    SUPPORTS = "SUPPORTS"
    REFUTES = "REFUTES"


_TERMINAL = {EvidenceStatus.SUPPORTS, EvidenceStatus.REFUTES}


@dataclass(frozen=True, slots=True)
class Evidence:
    evidence_id: str
    experiment_id: str
    candidate_id: str
    edge_id: str | None = None
    metrics: dict = field(default_factory=dict)
    artifacts: tuple[str, ...] = ()
    status: EvidenceStatus = EvidenceStatus.GENERATED
    created_at: datetime = field(default_factory=utcnow)

    def to_dict(self) -> dict:
        return {"evidence_id": self.evidence_id,
                "experiment_id": self.experiment_id,
                "candidate_id": self.candidate_id,
                "edge_id": self.edge_id,
                "metrics": self.metrics,
                "artifacts": list(self.artifacts),
                "status": self.status.value,
                "created_at": self.created_at.isoformat()}


def evidence_id(candidate_id: str, metrics: dict) -> str:
    """Deterministic EVID-ID (spec §2)."""
    canonical = json.dumps(metrics, sort_keys=True, default=str)
    h = hashlib.sha256(f"{candidate_id}|{canonical}".encode("utf-8")).hexdigest()
    return f"EVID-{h[:20]}"


class EvidenceRegistry(Registry[Evidence]):
    """Evidence registry (ADR-005 kernel, spec §4)."""

    kind = "evidence"
    identity_prefix = "EVID-"

    def _identity_of(self, entity: Evidence) -> str:
        return entity.evidence_id

    def all_supporting(self) -> list[RegistryEntry[Evidence]]:
        return [e for e in self.all_active() if e.entity.status == EvidenceStatus.SUPPORTS]

    def all_refuting(self) -> list[RegistryEntry[Evidence]]:
        return [e for e in self.all_active() if e.entity.status == EvidenceStatus.REFUTES]


def review(entry: RegistryEntry[Evidence], verdict: EvidenceStatus,
           edge_id: str | None = None,
           constitution_hash: str = CONSTITUTION_HASH) -> RegistryEntry[Evidence]:
    """Advance evidence lifecycle (spec §3): GENERATED → REVIEWED → SUPPORTS|REFUTES.

    Forward-only; terminal states are final.
    """
    cur = entry.entity
    if cur.status == EvidenceStatus.GENERATED:
        if verdict not in (EvidenceStatus.SUPPORTS, EvidenceStatus.REFUTES):
            raise ValueError("verdict must be SUPPORTS or REFUTES")
    elif cur.status == EvidenceStatus.REVIEWED:
        if verdict not in (EvidenceStatus.SUPPORTS, EvidenceStatus.REFUTES):
            raise ValueError("verdict must be SUPPORTS or REFUTES")
    else:
        raise ValueError(f"terminal state: {cur.status.value}")
    if verdict == EvidenceStatus.SUPPORTS and edge_id is None:
        raise ValueError("SUPPORTS requires edge_id (promotion target)")
    if verdict == EvidenceStatus.REFUTES and edge_id is not None:
        raise ValueError("REFUTES cannot carry edge_id")

    updated = Evidence(
        evidence_id=cur.evidence_id,
        experiment_id=cur.experiment_id,
        candidate_id=cur.candidate_id,
        edge_id=edge_id if verdict == EvidenceStatus.SUPPORTS else None,
        metrics=cur.metrics,
        artifacts=cur.artifacts,
        status=verdict,
        created_at=cur.created_at,
    )
    # advance the ACTIVE entry in place (same identity, new lifecycle status)
    return entry._registry.replace_entry(entry, updated)
