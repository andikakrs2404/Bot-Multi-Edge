"""AlphaOS Activation Engine: VALIDATED → ACTIVE.

The formal gatekeeper between Research and Production realms.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from .akb import AKB, NodeType
from .contracts import Edge, EdgeStatus, RelationshipType
from .evidence import Evidence
from .registries import EdgeRegistry


@dataclass(frozen=True, slots=True)
class ActivationPolicy:
    policy_id: str
    min_sharpe: float
    min_profit_factor: float
    max_evidence_age_days: int
    min_sample: int


@dataclass(frozen=True, slots=True)
class ActivationRecord:
    activation_id: str
    edge_id: str
    policy_id: str
    activated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    reason: str = "Activation policy met"


@dataclass(frozen=True, slots=True)
class DecayRecord:
    decay_id: str
    edge_id: str
    policy_id: str
    decayed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    reason: str = "Supporting evidence stale"


class ActivationEngine:
    def __init__(self, policy: ActivationPolicy, registry: EdgeRegistry, akb: AKB):
        self.policy = policy
        self.registry = registry
        self.akb = akb

    def activate(self, edge_id: str) -> ActivationRecord:
        entry = self.registry.latest_entry(edge_id)
        edge = entry.entity

        if edge.status != EdgeStatus.VALIDATED:
            raise ValueError("Only VALIDATED edges can be activated")

        evidence = self._supporting_evidence(edge)
        if not evidence:
            raise ValueError("Activation requires at least one supporting evidence")

        # Policy must be satisfied by all supporting evidence.
        for ev in evidence:
            self._check_policy(ev)

        self.registry.set_status(entry, EdgeStatus.ACTIVE)

        record = ActivationRecord(
            activation_id=f"ACT-{uuid.uuid4().hex[:12]}",
            edge_id=edge_id,
            policy_id=self.policy.policy_id,
        )
        self.akb.add_node(NodeType.ACTIVATION_RECORD, record.activation_id, record)
        self.akb.add_relationship(RelationshipType.ACTIVATED_BY,
                                  NodeType.EDGE, edge_id,
                                  NodeType.ACTIVATION_RECORD, record.activation_id)
        return record

    def decay(self, edge_id: str) -> DecayRecord | None:
        entry = self.registry.latest_entry(edge_id)
        edge = entry.entity

        if edge.status != EdgeStatus.ACTIVE:
            return None # only active edges can decay

        evidence = self._supporting_evidence(edge)
        if not evidence:
            return None # No evidence, can't check age.

        latest_evidence_date = max(ev.created_at for ev in evidence)
        if datetime.now(timezone.utc) - latest_evidence_date > timedelta(days=self.policy.max_evidence_age_days):
            self.registry.set_status(entry, EdgeStatus.DECAYED)
            record = DecayRecord(
                decay_id=f"DECAY-{uuid.uuid4().hex[:12]}",
                edge_id=edge_id,
                policy_id=self.policy.policy_id,
            )
            self.akb.add_node(NodeType.ACTIVATION_RECORD, record.decay_id, record)
            self.akb.add_relationship(RelationshipType.DECAYED_BY,
                                      NodeType.EDGE, edge_id,
                                      NodeType.ACTIVATION_RECORD, record.decay_id)
            return record
        return None

    def _supporting_evidence(self, edge: Edge) -> list[Evidence]:
        return [self.akb.get_node(NodeType.EVIDENCE, evid).payload
                for evid in edge.supported_by]

    def _check_policy(self, evidence: Evidence) -> None:
        checks = {
            "sharpe": (evidence.metrics.get("sharpe", 0.0), self.policy.min_sharpe),
            "profit_factor": (evidence.metrics.get("profit_factor", 0.0),
                              self.policy.min_profit_factor),
            "sample": (evidence.metrics.get("sample", 0), self.policy.min_sample),
        }
        for name, (got, need) in checks.items():
            if got < need:
                raise ValueError(
                    f"Policy '{self.policy.policy_id}' not met for {name}: {got} < {need}"
                )
