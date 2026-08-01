# Specification: Research Orchestrator (Edge Discovery Engine v1)

Derived from: ADR-007 (Experiment Protocol), ADR-001 (Determinism)
Constitution: be37bf97... (Freeze v1.0, 2026-07-29)

Status: Draft (v0.1)

## 1. Purpose

ResearchOrchestrator composes the research pipeline into one runnable
cycle: Dataset → FeatureFactory → RuleGenerator → ExperimentRunner →
Evidence → Validator → EdgeRanker → Top-N Edge.

Principle: **Orchestrator = Composition Layer, NOT Business Logic
Layer.** It contains no new logic — it wires existing engines.

## 2. Scope

Input:

```python
ResearchPolicy
Dataset
snapshot_dir (research snapshot, parquet with label_HIT_TARGET)
```

Output (single artifact, no side effects):

```python
ResearchCycleResult
```

STOPS at Ranked/Top-N Edge. Portfolio/Signal/Decision/Activation/Ledger/
Replay are OUT of scope.

## 3. ResearchPolicy

```python
@dataclass(frozen=True, slots=True)
class ResearchPolicy:
    policy_id: str
    rule_grid: dict[str, dict[str, list[float]]]   # RuleGenerator input
    ranking_policy: RankingPolicy
    validation_policy: ValidationPolicy
    top_n: int
```

## 4. ResearchCycleResult

```python
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
    promoted_edges: tuple[Edge, ...]    # top-N by rank
```

`cycle_id` = content hash of (policy_id, dataset_id, sorted rule_ids).

## 5. Flow

```text
generate rules (RuleGenerator)
→ register rules (RuleRegistry, cycle-scoped)
→ run experiment (ExperimentRunner, injected)
→ review evidence GENERATED→SUPPORTS (review())
→ validate → Edge(VALIDATED) (ValidatorEngine, cycle-scoped AKB)
→ rank (EdgeRanker)
→ top-N promote
```

All registries/AKB are CYCLE-SCOPED: fresh instances per run. The
orchestrator never touches the shared production AKB, Portfolio, or
Activation state. No global side effects.

## 6. Engine injection

Runner, validator, ranker are constructor-injected. This keeps the
orchestrator a pure composition layer and makes it testable with stub
engines.

## 7. Empty handling (no exceptions)

- Empty rule grid → empty result (all fields empty).
- No SUPPORTS evidence → validated_edges=(), ranked_edges=(),
  promoted_edges=().
- top_n=0 → promoted_edges=().

## 8. Determinism

Identical (policy, dataset, snapshot_dir, engines) → identical
cycle_id, same ranked order. Fresh cycle-scoped state per run.

## 9. Acceptance Criteria

- rules generated from grid, registered, run through injected runner
- SUPPORTS evidence → VALIDATED edges → ranked → top-N promoted
- cycle_id deterministic for identical inputs
- empty grid → empty result, no exception
- no evidence → empty validated/ranked/promoted
- cycle-scoped AKB: production AKB untouched (test asserts no write)
- promoted_edges == first top_n ranked edges
