"""AlphaOS Experiment Protocol (ADR-007, spec experiment-protocol).

Experiment = reproducible container: binds dataset + rules + registry
versions + constitution + seed + git into a deterministic fingerprint,
runs rule evaluation, emits Candidates with Evidence. Does NOT emit
Edge (Validator's job — domain boundary).

Research realm only: never touches production.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import Enum

import pyarrow.parquet as pq

from .contracts import CONSTITUTION_HASH, Rule, utcnow
from .registry import Registry
from .rules import parse
from .validation import dataset_id_of


class ExperimentStatus(str, Enum):
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class CandidateStatus(str, Enum):
    GENERATED = "GENERATED"
    VALIDATING = "VALIDATING"
    PASSED = "PASSED"
    FAILED = "FAILED"


def _sha(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def experiment_id(dataset_id: str, rule_ids: list[str], feature_registry_version: int,
                  label_registry_version: int, rule_registry_version: int,
                  git_commit: str, random_seed: int,
                  constitution_hash: str = CONSTITUTION_HASH) -> str:
    """Deterministic ExperimentID (spec §2)."""
    fp = _sha(dataset_id, "|".join(sorted(rule_ids)),
              str(feature_registry_version), str(label_registry_version),
              str(rule_registry_version), constitution_hash,
              git_commit, str(random_seed))
    return f"EXP-{fp[:20]}"


@dataclass(frozen=True, slots=True)
class Experiment:
    experiment_id: str
    dataset_id: str
    rule_ids: tuple[str, ...]
    feature_registry_version: int
    label_registry_version: int
    rule_registry_version: int
    constitution_hash: str = CONSTITUTION_HASH
    git_commit: str = ""
    random_seed: int = 42
    status: ExperimentStatus = ExperimentStatus.CREATED
    created_at: datetime = field(default_factory=utcnow)
    completed_at: datetime | None = None

    def fingerprint(self) -> str:
        return experiment_id(self.dataset_id, list(self.rule_ids),
                             self.feature_registry_version,
                             self.label_registry_version,
                             self.rule_registry_version,
                             self.git_commit, self.random_seed,
                             self.constitution_hash)

    def to_dict(self) -> dict:
        d = {
            "experiment_id": self.experiment_id,
            "dataset_id": self.dataset_id,
            "rule_ids": list(self.rule_ids),
            "feature_registry_version": self.feature_registry_version,
            "label_registry_version": self.label_registry_version,
            "rule_registry_version": self.rule_registry_version,
            "constitution_hash": self.constitution_hash,
            "git_commit": self.git_commit,
            "random_seed": self.random_seed,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
        return d


@dataclass(frozen=True, slots=True)
class Candidate:
    candidate_id: str
    rule_id: str
    experiment_id: str
    metrics: dict = field(default_factory=dict)
    status: CandidateStatus = CandidateStatus.GENERATED

    def to_dict(self) -> dict:
        return {"candidate_id": self.candidate_id, "rule_id": self.rule_id,
                "experiment_id": self.experiment_id, "metrics": self.metrics,
                "status": self.status.value}


@dataclass(frozen=True, slots=True)
class Evidence:
    evidence_id: str
    experiment_id: str
    candidate_id: str
    edge_id: str | None = None
    metrics: dict = field(default_factory=dict)
    artifacts: tuple[str, ...] = ()
    created_at: datetime = field(default_factory=utcnow)

    def to_dict(self) -> dict:
        return {"evidence_id": self.evidence_id,
                "experiment_id": self.experiment_id,
                "candidate_id": self.candidate_id, "edge_id": self.edge_id,
                "metrics": self.metrics, "artifacts": list(self.artifacts),
                "created_at": self.created_at.isoformat()}


def candidate_id(experiment_id: str, rule_id: str) -> str:
    return f"CAND-{_sha(experiment_id, rule_id)[:20]}"


def evidence_id(candidate_id: str, metrics: dict) -> str:
    canonical = json.dumps(metrics, sort_keys=True, default=str)
    return f"EVID-{_sha(candidate_id, canonical)[:20]}"


# ── metrics ──

MAX_PROFIT_FACTOR = 999.0
ANNUALIZATION_FACTOR = 252

# sample std (ddof=1) or tiny to avoid div-by-zero


def _sample_std(xs: list[float]) -> float:
    n = len(xs)
    if n < 2:
        return 0.0
    mean = sum(xs) / n
    return math.sqrt(sum((x - mean) ** 2 for x in xs) / (n - 1))


def compute_metrics(returns: list[float], n_total: int) -> dict:
    """Return-based candidate metrics (spec §5a).

    Deterministic. n==0 → zero metrics (valid result, not error).
    """
    n = len(returns)
    if n == 0:
        return {"trade_count": 0, "coverage": 0.0, "hit_rate": 0.0,
                "expectancy": 0.0, "profit_factor": 0.0,
                "max_drawdown": 0.0, "sharpe": 0.0}
    gross_win = sum(r for r in returns if r > 0)
    gross_loss = -sum(r for r in returns if r < 0)
    pf = MAX_PROFIT_FACTOR if gross_loss == 0.0 else gross_win / gross_loss
    mean = sum(returns) / n
    sd = _sample_std(returns)
    sharpe = (mean / sd * math.sqrt(ANNUALIZATION_FACTOR)) if sd else 0.0
    # max drawdown: peak-to-trough of cumulative returns, positive
    peak = 0.0
    max_dd = 0.0
    cum = 0.0
    for r in returns:
        cum += r
        peak = max(peak, cum)
        max_dd = max(max_dd, peak - cum)
    return {
        "trade_count": n,
        "coverage": n / n_total if n_total else 0.0,
        "hit_rate": sum(1 for r in returns if r > 0) / n,
        "expectancy": mean,
        "profit_factor": pf,
        "max_drawdown": max_dd,
        "sharpe": sharpe,
    }


# ── runner ──

@dataclass(frozen=True, slots=True)
class ExperimentResult:
    experiment: Experiment
    candidates: tuple[Candidate, ...]
    evidence: tuple[Evidence, ...]


class ExperimentRunner:
    """Evaluate rules against a research snapshot; emit candidates+evidence."""

    def __init__(self, git_commit: str = "", min_sample: int = 300,
                 min_hit_rate: float = 0.55) -> None:
        self.git_commit = git_commit
        self.min_sample = min_sample
        self.min_hit_rate = min_hit_rate

    def run(self, snapshot_dir, dataset_id: str, rule_ids: list[str],
            rule_registry: Registry | None = None,
            feature_registry_version: int = 0,
            label_registry_version: int = 0,
            rule_registry_version: int = 0,
            random_seed: int = 42,
            constitution_hash: str = CONSTITUTION_HASH) -> ExperimentResult:
        """Evaluate rules over a research snapshot (needs label_HIT_TARGET).

        rule_ids: canonical AST text OR RuleIDs resolved via rule_registry
        (ADR-006: identity from registry; unregistered rule = hard error).
        """
        asts: dict[str, object] = {}
        for rid in rule_ids:
            if rid.startswith("("):
                asts[rid] = parse(rid)
            else:
                if rule_registry is None:
                    raise ValueError(f"rule_registry required to resolve {rid}")
                rule = rule_registry.get(rid)  # raises if not ACTIVE
                asts[rid] = parse(rule.ast)
        exp = Experiment(
            experiment_id=experiment_id(dataset_id, rule_ids,
                                        feature_registry_version,
                                        label_registry_version,
                                        rule_registry_version,
                                        self.git_commit, random_seed,
                                        constitution_hash),
            dataset_id=dataset_id,
            rule_ids=tuple(rule_ids),
            feature_registry_version=feature_registry_version,
            label_registry_version=label_registry_version,
            rule_registry_version=rule_registry_version,
            constitution_hash=constitution_hash,
            git_commit=self.git_commit,
            random_seed=random_seed,
            status=ExperimentStatus.RUNNING,
        )

        table = pq.read_table(snapshot_dir / "snapshot.parquet")
        data = table.to_pylist()
        if not data or "label_HIT_TARGET" not in table.column_names:
            raise ValueError("snapshot must contain label_HIT_TARGET (research snapshot)")
        if "label_RETURN_1h" not in table.column_names:
            raise ValueError(
                "snapshot must contain label_RETURN_1h "
                "(return-based metrics, spec experiment-protocol §5a)")

        # per-symbol percentile/z-score (in-sample; rolling normalization later)
        ctx = _build_context(data)

        candidates: list[Candidate] = []
        evidence: list[Evidence] = []
        for rid in rule_ids:
            ast = asts[rid]
            matched = [row for row in data if _eval_row(ast, row, ctx)]
            returns = [row["label_RETURN_1h"] for row in matched]
            metrics = compute_metrics(returns, len(data))
            cid = candidate_id(exp.experiment_id, rid)
            passed = (metrics["trade_count"] >= self.min_sample
                      and metrics["hit_rate"] >= self.min_hit_rate)
            cand = Candidate(candidate_id=cid, rule_id=rid,
                             experiment_id=exp.experiment_id, metrics=metrics,
                             status=(CandidateStatus.PASSED if passed
                                     else CandidateStatus.FAILED))
            candidates.append(cand)
            evidence.append(Evidence(
                evidence_id=evidence_id(cid, metrics),
                experiment_id=exp.experiment_id, candidate_id=cid,
                metrics=metrics,
                artifacts=(str(snapshot_dir),),
            ))

        completed = replace(exp, status=ExperimentStatus.COMPLETED,
                            completed_at=utcnow())
        return ExperimentResult(completed, tuple(candidates), tuple(evidence))


def _eval_row(ast, row: dict, ctx: dict) -> bool:
    from .rules import evaluate, FeatureValue
    feats: dict = {}
    for name, sym_ctx in ctx.items():
        v = row.get(name, 0.0)
        m, s = sym_ctx[row["symbol"]]["mean"], sym_ctx[row["symbol"]]["sd"]
        feats[name] = FeatureValue(value=v if v == v else 0.0,
                                   percentile=_pct_from_z((v - m) / s if s else 0.0),
                                   zscore=(v - m) / s if s else 0.0)
    try:
        return evaluate(ast, feats)
    except KeyError:
        return False


def _pct_from_z(z: float) -> float:
    """Standard normal CDF → percentile 0..100 (approx)."""
    import math
    return 50.0 * (1.0 + math.erf(z / math.sqrt(2.0)))


def _build_context(data: list[dict]) -> dict:
    """{feature: {symbol: {pct, z}}} — in-sample stats per symbol."""
    import math
    ctx: dict = {}
    feat_names = [k for k in data[0].keys()
                  if k not in ("ts", "symbol", "exchange", "tier")
                  and not k.startswith("label_")]
    for name in feat_names:
        by_sym: dict = {}
        for row in data:
            by_sym.setdefault(row["symbol"], []).append(row[name])
        ctx[name] = {}
        for sym, vals in by_sym.items():
            valid = [v for v in vals if v == v]  # drop NaN
            if not valid:
                ctx[name][sym] = {"mean": 0.0, "sd": 1.0}
                continue
            mean = sum(valid) / len(valid)
            var = sum((v - mean) ** 2 for v in valid) / len(valid)
            sd = math.sqrt(var) or 1.0
            ctx[name][sym] = {"mean": mean, "sd": sd}
    return ctx


def write_artifacts(exp_dir, result: ExperimentResult) -> None:
    """Write experiment.json / candidates.json / evidence.json (spec §8)."""
    exp_dir.mkdir(parents=True, exist_ok=True)
    (exp_dir / "experiment.json").write_text(
        json.dumps(result.experiment.to_dict(), indent=2))
    (exp_dir / "candidates.json").write_text(
        json.dumps([c.to_dict() for c in result.candidates], indent=2))
    (exp_dir / "evidence.json").write_text(
        json.dumps([e.to_dict() for e in result.evidence], indent=2))
