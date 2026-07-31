"""AlphaOS Validator Engine: Evidence → Edge promotion.

Validator consumes Evidence(SUPPORTS), applies explicit ValidationPolicy,
and promotes to Edge(VALIDATED). No discovery, no backtest, no activation.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from .akb import AKB, NodeType, link_edge_evidence
from .contracts import Edge, EdgeStatus
from .evidence import Evidence, EvidenceStatus
from .registries import EdgeRegistry


@dataclass(frozen=True, slots=True)
class ValidationPolicy:
    policy_id: str
    min_sample: int
    min_hit_rate: float
    min_profit_factor: float
    min_sharpe: float


def edge_id(rule_id: str, evidence_ids: tuple[str, ...]) -> str:
    """Deterministic EdgeID from RuleID + sorted EvidenceIDs."""
    body = json.dumps({"rule_id": rule_id, "evidence_ids": sorted(evidence_ids)},
                      sort_keys=True)
    return f"EDGE-{hashlib.sha256(body.encode('utf-8')).hexdigest()[:20]}"


class ValidatorEngine:
    """Promote SUPPORTS Evidence into VALIDATED Edge."""

    def __init__(self, policy: ValidationPolicy, edge_registry: EdgeRegistry,
                 akb: AKB) -> None:
        self.policy = policy
        self.edge_registry = edge_registry
        self.akb = akb

    def promote(self, rule_id: str, evidence: list[Evidence]) -> Edge:
        """Validate Evidence list and register Edge(VALIDATED)."""
        if not evidence:
            raise ValueError("promotion requires at least one Evidence")
        self._validate_inputs(rule_id, evidence)
        evid_ids = tuple(sorted(e.evidence_id for e in evidence))
        exp_id = evidence[0].experiment_id
        edge = Edge(edge_id=edge_id(rule_id, evid_ids), rule_id=rule_id,
                    experiment_id=exp_id, supported_by=evid_ids,
                    policy_id=self.policy.policy_id,
                    status=EdgeStatus.VALIDATED)

        # Fail on duplicate before writing AKB facts.
        self.edge_registry.register(edge)
        self.akb.add_node(NodeType.EDGE, edge.edge_id, edge)
        for ev in sorted(evidence, key=lambda x: x.evidence_id):
            link_edge_evidence(self.akb, edge, ev)
        return edge

    def _validate_inputs(self, rule_id: str, evidence: list[Evidence]) -> None:
        exp_ids = {e.experiment_id for e in evidence}
        if len(exp_ids) != 1:
            raise ValueError("all evidence must share same experiment")
        for ev in evidence:
            if ev.status != EvidenceStatus.SUPPORTS:
                raise ValueError("Validator only consumes EvidenceStatus.SUPPORTS")
            metric_rule = ev.metrics.get("rule_id")
            if metric_rule is not None and metric_rule != rule_id:
                raise ValueError("evidence rule_id mismatch")
            self._check_policy(ev)

    def _check_policy(self, ev: Evidence) -> None:
        checks = {
            "sample": (ev.metrics.get("sample", 0), self.policy.min_sample),
            "hit_rate": (ev.metrics.get("hit_rate", 0.0), self.policy.min_hit_rate),
            "profit_factor": (ev.metrics.get("profit_factor", 0.0),
                              self.policy.min_profit_factor),
            "sharpe": (ev.metrics.get("sharpe", 0.0), self.policy.min_sharpe),
        }
        for name, (got, need) in checks.items():
            if got < need:
                raise ValueError(f"{name} below policy {self.policy.policy_id}: {got} < {need}")
