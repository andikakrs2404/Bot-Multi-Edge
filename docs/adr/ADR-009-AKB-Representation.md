# ADR-009: AKB Representation

- **Layer:** 1 (Domain & Contracts)
- **Status:** Draft
- **Date:** 2026-07-29
- **Depends On:** ADR-008

## Context

The Alpha Knowledge Base is the single source of truth of AlphaOS. Its *representation* must satisfy: immutability of artifacts, graph-shaped relationships, fast research queries, and safe read-only production access. This ADR fixes the representation; implementation details (DuckDB schema etc.) live in `docs/specifications/schemas/`.

## Decision

### Representation Principles

1. **The AKB is the persistent representation of the domain knowledge graph** (ADR-002). Storage technology may change; the AKB concept does not.
2. **Separation of artifact and index:** immutable artifacts (parquet, manifests) are the source of truth; database tables are indexes/views over them.
3. **Graph, not just tables:** relationships (`derives`, `produces`, `supersedes`, `allocated_to`, `drives`, `supported_by`) are first-class queryable edges with `RelationshipType` semantics (ADR-002).

### Logical Structure

```text
Alpha Knowledge Base
├── Registries        (datasets, features, labels, rules)
├── Experiments       (configs + results, incl. FAILED)
├── Evidence          (evidence bundles per candidate/edge)
├── Edges             (living records + lifecycle history)
├── Portfolios        (allocations over ACTIVE edges)
├── Production        (decisions, executions, settled outcomes)
└── Knowledge Graph   (relationship edges + lineage)
```

### Concurrency & Access

- **Research Realm:** read/write — writes only via engine artifacts (append-only; no in-place edits).
- **Production Realm:** read-only views over VALIDATED/ACTIVE knowledge + realtime feature snapshots. Enforced by trust model (ADR-000B).

### Physical Storage

- Recommended default: **DuckDB** over content-addressed **Parquet** files (columnar, cheap, SQL, directly reads parquet). Schema in `docs/specifications/schemas/akb.md`.
- Migration to other stores (PostgreSQL, ClickHouse, object storage) must preserve the logical structure above — the ontology must not change.

## Consequences

- **Positive:** Storage-agnostic; append-only history; cheap graph queries over parquet; production isolation by construction.
- **Negative:** Requires keeping artifact/index consistency discipline. Accepted.

## Alternatives Considered

- **AKB as a plain relational DB only:** Rejected — loses artifact immutability and graph semantics.
- **Graph DB (Neo4j) as primary:** Rejected for v1.0 — heavier ops, no native parquet; may become a secondary index later.

## Migration Path

Storage migration must be transparent to engines: engines depend on the logical AKB contract, not on DuckDB specifics.
