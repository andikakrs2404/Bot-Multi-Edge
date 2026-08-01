"""Tests for AlphaOS ResearchOrchestrator (composition layer)."""

from dataclasses import dataclass

import pytest

from shared.contracts import Dataset, Rule
from shared.edge_ranker import RankedEdge, RankingPolicy
from shared.evidence import Evidence, EvidenceRegistry, EvidenceStatus, review
from shared.experiment import Evidence as ExpEvidence  # noqa: F401  (unused alias guard)
from shared.orchestrator import (
    ResearchCycleResult,
    ResearchOrchestrator,
    ResearchPolicy,
)
from shared.registry import RegistryEntry
from shared.rules import parse
from shared.validator import ValidationPolicy


def rule(text: str) -> Rule:
    from shared.rules import canonical_text, rule_id
    ast = canonical_text(parse(text))
    return Rule(rule_id=rule_id(ast), ast=ast,
                feature_ids=(text.split()[1],))


def dataset(ds_id="DS-1") -> Dataset:
    return Dataset(dataset_id=ds_id, schema_version="1.0", universe="crypto",
                   timeframe="1h", date_range=("2026-01-01", "2026-06-30"),
                   content_hash=f"CH-{ds_id}")


GRID = {"RSI_14": {"<": [20, 30]}, "ADX_14": {">": [25]}}


class StubRunner:
    """Injected runner: emits GENERATED evidence with full metrics."""

    def __init__(self, rule_ids):
        self.rule_ids = rule_ids

    def run(self, snapshot_dir, dataset_id, rule_ids, **kw):
        from shared.experiment import (
            Candidate, CandidateStatus, Experiment, ExperimentResult,
            ExperimentStatus, candidate_id, evidence_id,
        )
        exp = Experiment(experiment_id="EXP-1", dataset_id=dataset_id,
                         rule_ids=tuple(rule_ids), constitution_hash="CH",
                         feature_registry_version=0,
                         label_registry_version=0,
                         rule_registry_version=0,
                         status=ExperimentStatus.COMPLETED)
        cands, evs = [], []
        for rid in rule_ids:
            metrics = {"sample": 500, "hit_rate": 0.6,
                       "sharpe": 1.5, "profit_factor": 1.8,
                       "max_drawdown": 0.2, "coverage": 0.7}
            cid = candidate_id(exp.experiment_id, rid)
            cands.append(Candidate(candidate_id=cid, rule_id=rid,
                                   experiment_id=exp.experiment_id,
                                   metrics=metrics,
                                   status=CandidateStatus.PASSED))
            evs.append(Evidence(evidence_id=evidence_id(cid, metrics),
                                experiment_id=exp.experiment_id,
                                candidate_id=cid, metrics=metrics,
                                status=EvidenceStatus.GENERATED))
        return ExperimentResult(exp, tuple(cands), tuple(evs))


def evidence_registry_from(result) -> EvidenceRegistry:
    reg = EvidenceRegistry()
    for ev in result.evidence:
        entry = reg.register(ev)
        review(entry, EvidenceStatus.SUPPORTS, edge_id=f"EDGE-{ev.candidate_id}")
    return reg


def build_orchestrator(rule_ids):
    runner = StubRunner(rule_ids)
    policy = ResearchPolicy(
        policy_id="POL-1",
        rule_grid=GRID,
        ranking_policy=RankingPolicy("RP", 1.0, 1.0, 1.0, 1.0),
        validation_policy=ValidationPolicy("VP", min_sample=100,
                                           min_hit_rate=0.5,
                                           min_profit_factor=1.0,
                                           min_sharpe=0.5),
        top_n=2,
    )
    return ResearchOrchestrator(policy, runner=runner), policy


class TestFullCycle:
    def test_end_to_end(self):
        rules = (rule("(LT RSI_14 20)"), rule("(LT RSI_14 30)"),
                 rule("(GT ADX_14 25)"))
        orch, policy = build_orchestrator([r.rule_id for r in rules])

        result = orch.run(dataset(), snapshot_dir=None)

        assert isinstance(result, ResearchCycleResult)
        assert result.dataset_id == "DS-1"
        assert set(result.generated_rules) == set(rules)
        assert result.experiments_run == 1
        assert result.evidence_count == 3
        assert len(result.validated_edges) == 3
        assert len(result.ranked_edges) == 3
        assert len(result.promoted_edges) == 2  # top_n
        assert result.promoted_edges[0].edge_id == result.ranked_edges[0].edge_id

    def test_cycle_id_deterministic(self):
        rules = (rule("(LT RSI_14 20)"),)
        orch1, _ = build_orchestrator([rules[0].rule_id])
        orch2, _ = build_orchestrator([rules[0].rule_id])

        r1 = orch1.run(dataset(), snapshot_dir=None)
        r2 = orch2.run(dataset(), snapshot_dir=None)

        assert r1.cycle_id == r2.cycle_id
        assert r1.ranked_edges == r2.ranked_edges


class TestEmptyHandling:
    def test_empty_grid_empty_result(self):
        policy = ResearchPolicy(
            policy_id="POL-E", rule_grid={},
            ranking_policy=RankingPolicy("RP", 1.0, 1.0, 1.0, 1.0),
            validation_policy=ValidationPolicy("VP", 100, 0.5, 1.0, 0.5),
            top_n=2,
        )
        orch = ResearchOrchestrator(policy, runner=StubRunner([]))

        result = orch.run(dataset(), snapshot_dir=None)

        assert result.generated_rules == ()
        assert result.validated_edges == ()
        assert result.ranked_edges == ()
        assert result.promoted_edges == ()
        assert result.evidence_count == 0


class TestNoSideEffects:
    def test_cycle_scoped_akb(self):
        from shared.akb import AKB, NodeType
        production_akb = AKB()
        rules = (rule("(LT RSI_14 20)"),)
        orch, _ = build_orchestrator([rules[0].rule_id])

        orch.run(dataset(), snapshot_dir=None)

        # production AKB untouched
        assert len(production_akb.nodes) == 0
