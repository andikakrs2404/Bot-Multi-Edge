"""Tests for AlphaOS Experiment Protocol (ADR-007, spec experiment-protocol)."""

import json
import math
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from shared.experiment import (
    Candidate,
    CandidateStatus,
    Evidence,
    Experiment,
    ExperimentResult,
    ExperimentRunner,
    ExperimentStatus,
    candidate_id,
    evidence_id,
    experiment_id,
    write_artifacts,
)
from shared.contracts import Rule
from shared.registries import RuleRegistry
from shared.rules import rule_id


def make_snapshot(tmp_path, n_bars=400, symbols=("BTCUSDT", "ETHUSDT"),
                  feature="RSI_14_CLOSE"):
    """Research snapshot: one feature + label_HIT_TARGET.

    RSI constructed so rule (GT RSI P90) matches ~10% of rows, half of
    which hit target → hit_rate ~0.5 (below/above threshold adjustable).
    """
    rows = []
    for sym in symbols:
        for i in range(n_bars):
            ts = 1_700_000_000_000 + i * 1_800_000
            rsi_val = 50.0 + 40.0 * math.sin(i / 7.0)  # -10..90
            hit = 1.0 if (i % 4 == 0 and rsi_val > 80) else 0.0
            rows.append({"ts": ts, "symbol": sym, "exchange": "binance_futures",
                         "tier": "A", feature: rsi_val,
                         "label_HIT_TARGET": hit})
    schema = pa.schema([
        ("ts", pa.int64()), ("symbol", pa.string()), ("exchange", pa.string()),
        ("tier", pa.string()), (feature, pa.float64()),
        ("label_HIT_TARGET", pa.float64()),
    ])
    t = pa.Table.from_arrays(
        [pa.array([r[k] for r in rows]) for k in schema.names], schema=schema)
    sd = tmp_path / "snap"
    sd.mkdir(parents=True)
    pq.write_table(t, sd / "snapshot.parquet")
    return sd


class TestIdentity:
    def test_experiment_id_deterministic(self):
        a = experiment_id("ds1", ["(GT A P80)"], 1, 2, 3, "abc", 42)
        b = experiment_id("ds1", ["(GT A P80)"], 1, 2, 3, "abc", 42)
        assert a == b
        assert a.startswith("EXP-")

    def test_experiment_id_changes_on_input(self):
        base = experiment_id("ds1", ["(GT A P80)"], 1, 2, 3, "abc", 42)
        assert experiment_id("ds2", ["(GT A P80)"], 1, 2, 3, "abc", 42) != base
        assert experiment_id("ds1", ["(GT A P90)"], 1, 2, 3, "abc", 42) != base
        assert experiment_id("ds1", ["(GT A P80)"], 2, 2, 3, "abc", 42) != base
        assert experiment_id("ds1", ["(GT A P80)"], 1, 2, 3, "abd", 42) != base
        assert experiment_id("ds1", ["(GT A P80)"], 1, 2, 3, "abc", 43) != base

    def test_candidate_evidence_ids(self):
        c = candidate_id("EXP-abc", "(GT A P80)")
        assert c.startswith("CAND-")
        assert candidate_id("EXP-abc", "(GT A P80)") == c
        e = evidence_id(c, {"sample": 100, "hit_rate": 0.6})
        assert e.startswith("EVID-")
        assert evidence_id(c, {"hit_rate": 0.6, "sample": 100}) == e  # sorted

    def test_rule_order_insensitive(self):
        a = experiment_id("ds1", ["(GT B P70)", "(GT A P80)"], 1, 2, 3, "g", 42)
        b = experiment_id("ds1", ["(GT A P80)", "(GT B P70)"], 1, 2, 3, "g", 42)
        assert a == b  # sorted rule_ids


class TestExperiment:
    def test_fields_recorded(self):
        e = Experiment(
            experiment_id="EXP-1", dataset_id="ds1",
            rule_ids=("(GT A P80)",),
            feature_registry_version=4, label_registry_version=2,
            rule_registry_version=9, git_commit="deadbeef", random_seed=7,
        )
        d = e.to_dict()
        assert d["git_commit"] == "deadbeef"
        assert d["random_seed"] == 7
        assert d["constitution_hash"].startswith("be37bf97")
        assert d["status"] == "CREATED"

    def test_fingerprint_matches_id(self):
        e = Experiment(
            experiment_id="", dataset_id="ds1", rule_ids=("(GT A P80)",),
            feature_registry_version=1, label_registry_version=2,
            rule_registry_version=3, git_commit="g", random_seed=42,
        )
        fp = e.fingerprint()
        assert fp == experiment_id("ds1", ["(GT A P80)"], 1, 2, 3, "g", 42)


class TestRunner:
    def test_run_produces_candidates_and_evidence(self, tmp_path):
        sd = make_snapshot(tmp_path)
        runner = ExperimentRunner(git_commit="abc", min_sample=10, min_hit_rate=0.3)
        rule = "(GT RSI_14_CLOSE P80)"
        res = runner.run(sd, "ds1", [rule], 1, 1, 1)
        assert res.experiment.status == ExperimentStatus.COMPLETED
        assert res.experiment.completed_at is not None
        assert len(res.candidates) == 1
        assert len(res.evidence) == 1
        c = res.candidates[0]
        assert c.experiment_id == res.experiment.experiment_id
        assert c.rule_id == rule
        assert c.metrics["sample"] > 0
        assert 0.0 <= c.metrics["hit_rate"] <= 1.0
        ev = res.evidence[0]
        assert ev.candidate_id == c.candidate_id
        assert ev.experiment_id == res.experiment.experiment_id
        assert ev.edge_id is None  # promotion is validator's job

    def test_passed_failed_status(self, tmp_path):
        sd = make_snapshot(tmp_path)
        # impossible rule → sample=0 → FAILED
        runner = ExperimentRunner(min_sample=10, min_hit_rate=0.3)
        res = runner.run(sd, "ds1", ["(GT RSI_14_CLOSE P99)"], 1, 1, 1)
        assert res.candidates[0].status == CandidateStatus.FAILED
        # permissive thresholds → PASSED (same rule still matches rows at P99
        # percentile — z-based percentile is normal CDF, so ~0.13% of rows)
        runner2 = ExperimentRunner(min_sample=1, min_hit_rate=0.0)
        res2 = runner2.run(sd, "ds1", ["(GT RSI_14_CLOSE P80)"], 1, 1, 1)
        assert res2.candidates[0].status == CandidateStatus.PASSED

    def test_requires_label(self, tmp_path):
        rows = [{"ts": 1, "symbol": "X", "exchange": "e", "tier": "A",
                 "RSI_14_CLOSE": 50.0}]
        schema = pa.schema([("ts", pa.int64()), ("symbol", pa.string()),
                            ("exchange", pa.string()), ("tier", pa.string()),
                            ("RSI_14_CLOSE", pa.float64())])
        t = pa.Table.from_arrays([pa.array([r[k] for r in rows]) for k in schema.names],
                                 schema=schema)
        sd = tmp_path / "snap2"
        sd.mkdir()
        pq.write_table(t, sd / "snapshot.parquet")
        runner = ExperimentRunner()
        with pytest.raises(ValueError):
            runner.run(sd, "ds1", ["(GT RSI_14_CLOSE P80)"], 1, 1, 1)

    def test_rule_by_registry_id(self, tmp_path):
        sd = make_snapshot(tmp_path)
        reg = RuleRegistry()
        rid = rule_id("(GT RSI_14_CLOSE P80)")
        reg.register(Rule(rule_id=rid, ast="(GT RSI_14_CLOSE P80)"))
        runner = ExperimentRunner(min_sample=10, min_hit_rate=0.3)
        res = runner.run(sd, "ds1", [rid], reg, 1, 1, 1)
        assert res.candidates[0].rule_id == rid

    def test_unregistered_rule_id_rejected(self, tmp_path):
        sd = make_snapshot(tmp_path)
        runner = ExperimentRunner()
        with pytest.raises(Exception):
            runner.run(sd, "ds1", ["RULE-deadbeef"], None, 1, 1, 1)


class TestArtifacts:
    def test_write_artifacts(self, tmp_path):
        exp = Experiment(experiment_id="EXP-x", dataset_id="ds1",
                         rule_ids=("r",), feature_registry_version=1,
                         label_registry_version=1, rule_registry_version=1)
        cand = Candidate(candidate_id="CAND-1", rule_id="r",
                         experiment_id="EXP-x", metrics={"sample": 5},
                         status=CandidateStatus.PASSED)
        ev = Evidence(evidence_id="EVID-1", experiment_id="EXP-x",
                      candidate_id="CAND-1", metrics={"sample": 5})
        out = tmp_path / "exp"
        write_artifacts(out, ExperimentResult(exp, (cand,), (ev,)))
        assert (out / "experiment.json").exists()
        assert (out / "candidates.json").exists()
        assert (out / "evidence.json").exists()
        d = json.loads((out / "candidates.json").read_text())
        assert d[0]["candidate_id"] == "CAND-1"
