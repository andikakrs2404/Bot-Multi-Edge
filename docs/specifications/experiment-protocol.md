# Specification: Experiment Protocol

Derived from: ADR-007 (Experiment Protocol), ADR-002 (Domain Ontology), ADR-005 (Registry Model), ADR-006 (Rule Grammar)
Constitution: be37bf97... (Freeze v1.0, 2026-07-29)

Status: Draft (v0.1)

## 1. Purpose

Experiment = **reproducible container**, not an optimizer. It binds
inputs (dataset, rules, registries, constitution, seed, git) into one
deterministic fingerprint, runs rule evaluation, and emits Candidates
with Evidence. It does NOT emit Edge — that is Validator's job.

## 2. Experiment Identity (Fingerprint)

```text
ExperimentID = EXP-<sha256(fingerprint_components)[:20]>

fingerprint_components:
  dataset_id
  rule_ids               (sorted)
  feature_registry_version
  label_registry_version
  rule_registry_version
  constitution_hash
  git_commit
  random_seed
```

Identical inputs ⇒ identical ExperimentID (reproducibility, ADR-001).
Registry versions come from the registries at creation time (ADR-005).

## 3. Experiment Fields

```text
experiment_id, dataset_id, rule_ids,
feature_registry_version, label_registry_version, rule_registry_version,
constitution_hash, git_commit, random_seed,
status, created_at, completed_at
```

## 4. Lifecycle

```text
CREATED → RUNNING → COMPLETED
                  ↘ FAILED
```

## 5. Candidate

One Candidate per (experiment, rule):

```text
candidate_id = CAND-<sha256(experiment_id + rule_id)[:20]>
rule_id, experiment_id, metrics, status
```

## 5a. Metrics (return-based, v0.1)

Snapshot MUST contain `label_RETURN_1h` (forward 1-bar return per row)
in addition to `label_HIT_TARGET`. Missing return column → hard error
(fail-closed, ADR-000B) — never silently fall back to hit-rate-only.

Matched rows (rule fired) produce a return series r_1..r_n, n = trade_count:

```text
trade_count     = n
coverage        = n / total_rows
hit_rate        = count(r > 0) / n
expectancy      = mean(r)
profit_factor   = gross_win / abs(gross_loss)
                  gross_win  = sum(r > 0)
                  gross_loss = sum(r < 0)
                  gross_loss == 0 → MAX_PROFIT_FACTOR = 999.0
sharpe          = mean(r) / (std(r, ddof=1) or tiny) * sqrt(ANNUALIZATION_FACTOR)
max_drawdown    = -min_k(cum_k / peak_k - 1)        # positive number
```

Constants:

```text
MAX_PROFIT_FACTOR = 999.0   (json-serializable, deterministic)
ANNUALIZATION_FACTOR = 252  (configurable via MetricPolicy; per-timeframe later)
```

`n == 0` → all metrics zero, `trade_count == 0` (valid experiment
result, not an error).

Metrics dict:

```text
{
  "trade_count", "coverage", "hit_rate", "expectancy",
  "sharpe", "profit_factor", "max_drawdown"
}
```

## 6. Evidence

One Evidence per candidate (immutable):

```text
evidence_id = EVID-<sha256(candidate_id + canonical metrics)[:20]>
experiment_id, candidate_id, edge_id (null until promotion),
metrics, artifacts, created_at
```

## 7. Evaluation Semantics

- Snapshot must contain `label_HIT_TARGET` AND `label_RETURN_1h`
  (research snapshot, ADR-005; return column mandatory since v0.1
  metrics expansion).
- Per symbol: percentile + z-score computed over the snapshot's rows
  (in-sample; rolling normalization is a later stage — `ponytail`).
- Rule matched at row ⇒ trade. Metrics from return series (see §5a).

## 8. Artifacts

```text
data/experiments/<experiment_id>/
    experiment.json
    candidates.json
    evidence.json
```

## 9. Acceptance Criteria

- ExperimentID + fingerprint deterministic (same inputs → same id)
- seed, git_commit, constitution_hash, registry versions recorded
- Candidate → Experiment, Evidence → Candidate → Experiment traceable
- lifecycle CREATED → RUNNING → COMPLETED | FAILED
- artifacts written under data/experiments/<id>/
