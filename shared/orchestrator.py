"""AlphaOS ResearchOrchestrator: Edge Discovery Engine v1.

Composition layer only — wires existing engines:
Dataset → FeatureFactory → RuleGenerator → ExperimentRunner → Evidence
→ Validator → EdgeRanker → Top-N Edge.

Cycle-scoped state: fresh registries/AKB per run. Never touches
production AKB, Portfolio, or Activation.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from .akb import AKB, NodeType
from .contracts import CONSTITUTION_HASH, Dataset, Edge, Rule, content_hash
from .edge_ranker import DEFAULT_RANKING_POLICY, RankedEdge, RankingPolicy, rank
from .evidence import EvidenceRegistry, EvidenceStatus, review
from .registries import EdgeRegistry, RuleRegistry
from .rule_generator import generate as generate_rules
from .validator import ValidationPolicy, ValidatorEngine


@dataclass(frozen=True, slots=True)
class ResearchPolicy:
    policy_id: str
    rule_grid: dict[str, dict[str, list[float]]]
    ranking_policy: RankingPolicy = DEFAULT_RANKING_POLICY
    validation_policy: ValidationPolicy | None = None
    top_n: int = 10


@dataclass(frozen=True, slots=True)
class ResearchCycleResult:
    cycle_id: str
    dataset_id: str
    constitution_hash: str
    generated_rules: tuple[Rule, ...]
    experiments_run: int
    evidence_count: int
    validated_edges: tuple[Edge, ...]
    ranked_edges: tuple[RankedEdge, ...]
    promoted_edges: tuple[Edge, ...]


class ResearchOrchestrator:
    def __init__(self, policy: ResearchPolicy, runner=None) -> None:
        self.policy = policy
        self.runner = runner  # injected ExperimentRunner (or stub)

    def run(self, dataset: Dataset, snapshot_dir) -> ResearchCycleResult:
        rules = generate_rules(self.policy.rule_grid)
        rule_ids = [r.rule_id for r in rules]

        if not rule_ids or self.runner is None:
            return ResearchCycleResult(
                cycle_id=self._cycle_id(dataset.dataset_id, rule_ids),
                dataset_id=dataset.dataset_id,
                constitution_hash=CONSTITUTION_HASH,
                generated_rules=rules,
                experiments_run=0,
                evidence_count=0,
                validated_edges=(),
                ranked_edges=(),
                promoted_edges=(),
            )

        # cycle-scoped state
        rule_registry = RuleRegistry()
        for r in rules:
            rule_registry.register(r)
        evidence_registry = EvidenceRegistry()
        edge_registry = EdgeRegistry()
        akb = AKB()

        result = self.runner.run(snapshot_dir, dataset.dataset_id, rule_ids,
                                 rule_registry=rule_registry)

        # GENERATED → SUPPORTS (attach edge_id per candidate)
        supporting: dict[str, object] = {}
        for ev in result.evidence:
            entry = evidence_registry.register(ev)
            edge_id = f"EDGE-{ev.candidate_id}"
            reviewed = review(entry, EvidenceStatus.SUPPORTS, edge_id=edge_id)
            supporting[ev.candidate_id] = reviewed.entity

        validator = ValidatorEngine(self.policy.validation_policy,
                                    edge_registry, akb)
        validated: list[Edge] = []
        for cand in result.candidates:
            ev = supporting.get(cand.candidate_id)
            if ev is not None and ev.status == EvidenceStatus.SUPPORTS:
                akb.add_node(NodeType.EVIDENCE, ev.evidence_id, ev)
                validated.append(validator.promote(cand.rule_id, [ev]))

        validated_edges = tuple(validated)
        ranked_edges = rank(validated_edges, self.policy.ranking_policy,
                            evidence_registry)
        promoted = tuple(
            e for e in validated_edges
            if e.edge_id in {r.edge_id for r in ranked_edges[:self.policy.top_n]}
        )

        return ResearchCycleResult(
            cycle_id=self._cycle_id(dataset.dataset_id, rule_ids),
            dataset_id=dataset.dataset_id,
            constitution_hash=CONSTITUTION_HASH,
            generated_rules=rules,
            experiments_run=1,
            evidence_count=len(result.evidence),
            validated_edges=validated_edges,
            ranked_edges=ranked_edges,
            promoted_edges=promoted,
        )

    def _cycle_id(self, dataset_id: str, rule_ids: list[str]) -> str:
        return content_hash({
            "policy_id": self.policy.policy_id,
            "dataset_id": dataset_id,
            "rule_ids": sorted(rule_ids),
        })
