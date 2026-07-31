# ADR-002: Domain Ontology

- **Layer:** 1 (Domain & Contracts)
- **Status:** Draft
- **Date:** 2026-07-29
- **Depends On:** ADR-000A, ADR-001

## Context

Before any contract or schema exists, the system must fix WHAT exists in its world. This ADR codifies the ontology of AlphaOS: the entities, their relationships, and the epistemological chain that gives Knowledge its meaning. It is intentionally free of implementation detail (see `docs/specifications/` for attributes).

## Decision

### The Epistemological Chain

Knowledge in AlphaOS follows a fixed chain of being. Each step earns more trust (ADR-000B):

```text
Observation → Evidence → Hypothesis → Experiment → Validation → Knowledge
```

An **Edge is Knowledge**. **Evidence supports Knowledge.** The two are distinct and must never be conflated.

### The Realms and the Shared Truth

```text
              AlphaOS
                 │
   ┌─────────────┼─────────────┐
Research Realm           Production Realm
   │                             │
   └─────────────┬───────────────┘
         Alpha Knowledge Base (AKB)
```

The AKB is **shared truth**. It belongs to neither realm. Research writes to it; Production reads from it.

### Core Entities

| Entity | Kind | Nature |
| --- | --- | --- |
| `ResearchCycle` | Aggregate Root | A complete scheduled run of the research pipeline. |
| `Dataset` | Entity | Immutable, versioned collection of market data. |
| `Feature` | Entity | An immutable derived property of market state. Evolution creates a NEW Feature; identity never changes. |
| `Label` | Entity | A future outcome used only in research. |
| `Rule` | Entity | A logical AST expression over Features. |
| `Candidate` | Entity | A Rule under evaluation, owned by one Experiment. |
| `Experiment` | Aggregate Root | A reproducible scientific inquiry. |
| `Evidence` | Entity | Statistical results supporting or refuting a Candidate. |
| `Edge` | Aggregate Root | A Candidate promoted to Knowledge. A living entity with a lifecycle. |
| `Portfolio` | Aggregate Root | A curated allocation over Active Edges. |
| `ProductionDecision` | Aggregate Root | An auditable action by the Production Engine. |

### Relationships

Relationships are NOT domain entities. They are properties of the knowledge graph. What is a first-class domain concept is the **RelationshipType**:

- `derives` (Feature → Feature, lineage)
- `uses` (Rule → Feature)
- `tests` (Experiment → Candidate)
- `produces` (Experiment → Edge)
- `supported_by` (Edge → Evidence)
- `supersedes` (Edge → Edge)
- `allocated_to` (Edge → Portfolio)
- `drives` (Portfolio → ProductionDecision)

Relationship *instances* are graph edges inside the AKB, queryable but not standalone domain objects.

### Domain Axioms

1. Knowledge grows; it is never overwritten.
2. Every claim must have Evidence.
3. Production never invents knowledge.
4. Research is reproducible.
5. Identity is permanent.

### Domain Invariants

1. Immutability: Dataset, Evidence, Experiment artifacts are write-once.
2. Unique provenance: an Edge is born from exactly one Experiment.
3. Lifecycle integrity: states transition only along legal paths (ADR-002A).
4. Portfolio soundness: a Portfolio contains only ACTIVE Edges.
5. Traceability: every ProductionDecision references a PortfolioID; every Edge references its ExperimentID.
6. AST canonical form: every Rule has a canonical AST, so RuleIDs hash deterministically.

## Consequences

- **Positive:** A stable, technology-agnostic ontology; clean epistemological separation; graph-native model ready for any storage.
- **Negative:** New entity types require a superseding ADR. Accepted.

## Alternatives Considered

- **Relationship as entity:** Rejected — DDD-wise it is a graph property, not a domain object.
- **Edge as evidence:** Rejected — conflates Knowledge with its proof, weakening the model.

## Migration Path

None for v1.0.
