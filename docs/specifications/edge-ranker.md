# Specification: Edge Ranker

Derived from: ADR-002A (Lifecycles), ADR-001 (Determinism)
Constitution: be37bf97... (Freeze v1.0, 2026-07-29)

Status: Draft (v0.1)

## 1. Purpose

EdgeRanker ranks VALIDATED/ACTIVE Edges by a weighted metric score. It
answers: "which edge is best?" — the priority input for Activation and
Portfolio selection.

## 2. Input

```text
tuple[Edge, ...]
RankingPolicy
```

Evidence lookup: metrics come from the Edges' supporting Evidence
(edge.supported_by → EvidenceRegistry). Missing evidence → error
(fail-closed).

## 3. RankingPolicy

```python
@dataclass(frozen=True, slots=True)
class RankingPolicy:
    policy_id: str
    sharpe_weight: float
    pf_weight: float
    dd_weight: float
    coverage_weight: float
```

Weights are NOT normalized in v0.1 — the caller supplies weights that
sum as intended. Default policy provided.

## 4. Score

```text
score =
  sharpe_weight   * sharpe
+ pf_weight       * profit_factor
- dd_weight       * max_drawdown     # drawdown penalized
+ coverage_weight * coverage
```

## 5. RankedEdge

```python
@dataclass(frozen=True, slots=True)
class RankedEdge:
    edge_id: str
    score: float
    rank: int
    component_scores: dict[str, float]   # sharpe, pf, dd, coverage
```

`component_scores["dd"]` stores the RAW drawdown (positive number);
the penalty is applied only in `score`.

## 6. Invariants

1. Deterministic: same (edges, policy) → same ranking.
2. Tie-break: equal score → sort by edge_id.
3. Reject edges with status RETIRED or DECAYED (not eligible for
   promotion/activation). VALIDATED + ACTIVE allowed.
4. Empty input → empty output, no error.
5. Missing evidence for an edge → error (no silent zero-score).

## 7. Acceptance Criteria

- higher sharpe ranks higher (weights 1,0,0,0)
- drawdown penalizes score
- tie → edge_id order
- RETIRED/DECAYED rejected
- empty → ()
- deterministic twice
- component_scores populated
