"""Tests for AlphaOS EdgeRanker (weighted metric ranking)."""

import pytest

from shared.contracts import Edge, EdgeStatus
from shared.edge_ranker import (
    RankedEdge,
    RankingPolicy,
    RankEdgeError,
    rank,
)
from shared.evidence import Evidence, EvidenceRegistry, EvidenceStatus, evidence_id


def make_edge(edge_id: str, metrics: dict, status=EdgeStatus.VALIDATED,
              registry=None) -> Edge:
    e = Evidence(
        evidence_id=evidence_id(f"CAND-{edge_id}", metrics),
        experiment_id="EXP-1",
        candidate_id=f"CAND-{edge_id}",
        metrics=metrics,
        status=EvidenceStatus.SUPPORTS,
    )
    if registry is not None:
        registry.register(e)
    return Edge(edge_id=edge_id, rule_id=f"RULE-{edge_id}",
                experiment_id="EXP-1", supported_by=(e.evidence_id,),
                policy_id="pol", status=status)


def build(edges_specs):
    reg = EvidenceRegistry()
    edges = tuple(make_edge(eid, metrics, status, reg)
                  for eid, metrics, status in edges_specs)
    return edges, reg


POL = RankingPolicy("pol", 1.0, 1.0, 1.0, 1.0)


class TestScoring:
    def test_sharpe_dominates(self):
        edges, reg = build([
            ("EDGE-A", {"sharpe": 2.0, "profit_factor": 1.0,
                        "max_drawdown": 0.1, "coverage": 0.5},
             EdgeStatus.VALIDATED),
            ("EDGE-B", {"sharpe": 1.0, "profit_factor": 1.0,
                        "max_drawdown": 0.1, "coverage": 0.5},
             EdgeStatus.VALIDATED),
        ])
        policy = RankingPolicy("p", 1.0, 0.0, 0.0, 0.0)

        out = rank(edges, policy, reg)

        assert out[0].edge_id == "EDGE-A"

    def test_drawdown_penalizes(self):
        edges, reg = build([
            ("EDGE-A", {"sharpe": 1.0, "profit_factor": 1.0,
                        "max_drawdown": 0.5, "coverage": 0.5},
             EdgeStatus.VALIDATED),
            ("EDGE-B", {"sharpe": 1.0, "profit_factor": 1.0,
                        "max_drawdown": 0.1, "coverage": 0.5},
             EdgeStatus.VALIDATED),
        ])
        policy = RankingPolicy("p", 0.0, 0.0, 1.0, 0.0)

        out = rank(edges, policy, reg)

        assert out[0].edge_id == "EDGE-B"

    def test_score_formula(self):
        edges, reg = build([
            ("EDGE-A", {"sharpe": 2.0, "profit_factor": 1.5,
                        "max_drawdown": 0.2, "coverage": 0.4},
             EdgeStatus.VALIDATED),
        ])
        policy = RankingPolicy("p", 1.0, 1.0, 1.0, 1.0)

        out = rank(edges, policy, reg)

        assert out[0].score == pytest.approx(2.0 + 1.5 - 0.2 + 0.4)
        assert out[0].component_scores == {
            "sharpe": 2.0, "pf": 1.5, "dd": 0.2, "coverage": 0.4}


class TestTieBreak:
    def test_equal_score_sorted_by_edge_id(self):
        m1 = {"sharpe": 1.0, "profit_factor": 1.0,
              "max_drawdown": 0.1, "coverage": 0.5}
        m2 = {"sharpe": 1.0, "profit_factor": 1.0,
              "max_drawdown": 0.1, "coverage": 0.5}
        edges, reg = build([
            ("EDGE-B", m1, EdgeStatus.VALIDATED),
            ("EDGE-A", m2, EdgeStatus.VALIDATED),
        ])
        policy = RankingPolicy("p", 1.0, 1.0, 1.0, 1.0)

        out = rank(edges, policy, reg)

        assert [r.edge_id for r in out] == ["EDGE-A", "EDGE-B"]


class TestReject:
    @pytest.mark.parametrize("status", [EdgeStatus.RETIRED, EdgeStatus.DECAYED])
    def test_rejects_retired_decayed(self, status):
        edges, reg = build([
            ("EDGE-A", {"sharpe": 1.0, "profit_factor": 1.0,
                        "max_drawdown": 0.1, "coverage": 0.5}, status),
        ])
        with pytest.raises(RankEdgeError, match="eligible"):
            rank(edges, POL, reg)

    def test_accepts_validated_active(self):
        for status in (EdgeStatus.VALIDATED, EdgeStatus.ACTIVE):
            edges, reg = build([
                ("EDGE-A", {"sharpe": 1.0, "profit_factor": 1.0,
                            "max_drawdown": 0.1, "coverage": 0.5}, status),
            ])
            assert len(rank(edges, POL, reg)) == 1

    def test_missing_evidence_rejected(self):
        edge = Edge(edge_id="EDGE-X", rule_id="RULE-X", experiment_id="EXP-1",
                    supported_by=("EVID-NOPE",), status=EdgeStatus.VALIDATED)
        with pytest.raises(RankEdgeError, match="evidence"):
            rank((edge,), POL, EvidenceRegistry())


class TestDeterminismAndEmpty:
    def test_empty_input_empty_output(self):
        assert rank((), POL, EvidenceRegistry()) == ()

    def test_deterministic_twice(self):
        edges, reg = build([
            ("EDGE-A", {"sharpe": 2.0, "profit_factor": 1.0,
                        "max_drawdown": 0.1, "coverage": 0.5},
             EdgeStatus.VALIDATED),
            ("EDGE-B", {"sharpe": 1.5, "profit_factor": 1.2,
                        "max_drawdown": 0.3, "coverage": 0.8},
             EdgeStatus.VALIDATED),
        ])
        assert rank(edges, POL, reg) == rank(edges, POL, reg)

    def test_rank_numbers_are_1_based(self):
        edges, reg = build([
            ("EDGE-A", {"sharpe": 2.0, "profit_factor": 1.0,
                        "max_drawdown": 0.1, "coverage": 0.5},
             EdgeStatus.VALIDATED),
            ("EDGE-B", {"sharpe": 1.0, "profit_factor": 1.0,
                        "max_drawdown": 0.1, "coverage": 0.5},
             EdgeStatus.VALIDATED),
        ])
        out = rank(edges, RankingPolicy("p", 1.0, 0.0, 0.0, 0.0), reg)
        assert [r.rank for r in out] == [1, 2]
