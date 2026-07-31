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

Metrics (this stage): `sample`, `hit_rate`.

Lifecycle: `GENERATED → VALIDATING → PASSED | FAILED`

Acceptance (defaults, configurable): `sample >= 300 AND hit_rate >= 0.55`
(per research schema; runner takes min_sample/min_hit_rate params).

## 6. Evidence

One Evidence per candidate (immutable):

```text
evidence_id = EVID-<sha256(candidate_id + canonical metrics)[:20]>
experiment_id, candidate_id, edge_id (null until promotion),
metrics, artifacts, created_at
```

## 7. Evaluation Semantics

- Snapshot must contain `label_HIT_TARGET` (research snapshot, ADR-005).
- Per symbol: percentile + z-score computed over the snapshot's rows
  (in-sample; rolling normalization is a later stage — `ponytail`).
- Rule matched at row ⇒ sample. `hit_rate = mean(HIT_TARGET | matched)`.

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
