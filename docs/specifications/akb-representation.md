# Specification: AKB Representation

Derived from: ADR-009 (AKB Representation), ADR-002 (Domain Ontology), ADR-008 (Evidence Model)
Constitution: be37bf97... (Freeze v1.0, 2026-07-29)

Status: Draft (v0.1)

## 1. Purpose

AKB = Alpha Knowledge Base: a **knowledge graph contract**, not a
storage engine. Ontology is truth; storage is implementation detail.
DuckDB may be the first physical representation, but ADR-009 defines
node types, relationship types, and query guarantees.

## 2. Node Types

```text
Dataset
Feature
Label
Rule
Experiment
Candidate
Evidence
Edge
Portfolio
ProductionDecision
```

## 3. Relationship Types

```text
USES          Rule → Feature | Experiment → Dataset | Experiment → Rule
PRODUCES      Experiment → Candidate | Experiment → Evidence
SUPPORTED_BY  Edge → Evidence          (1:N, mandatory)
SUPERSEDES    Edge → Edge | Dataset → Dataset | Rule → Rule
ALLOCATED_TO  Edge → Portfolio
DRIVES        Portfolio → ProductionDecision
REFERENCES    Evidence → Experiment | Evidence → Candidate
DERIVED_FROM  Feature → Dataset | Feature → Feature | Label → Dataset
```

## 4. Core Graph Guarantees

### 4.1 Edge evidence is 1:N

```text
Edge.supported_by = [EvidenceID, ...]
```

Rationale: initial validation, walk-forward, OOS, decay check, and
revalidation all produce separate Evidence records. AKB must keep all.

### 4.2 Evidence traceability

```text
Evidence → Candidate → Experiment → Dataset
Evidence → Experiment
```

### 4.3 Production traceability

```text
ProductionDecision → Portfolio → Edge → Evidence → Experiment → Dataset
```

### 4.4 No orphan knowledge

Edges must have at least one SUPPORTS Evidence before ACTIVE.
ProductionDecision must trace to at least one ACTIVE Edge.

## 5. Query Guarantees

AKB implementation must support:

```text
Given EdgeID:
  find all Evidence

Given EvidenceID:
  find Candidate and Experiment

Given ProductionDecisionID:
  trace to Portfolio, Edge(s), Evidence, Experiment, Dataset

Given EdgeID:
  trace to Dataset(s)

Given RuleID:
  find Experiments and Candidates using it
```

## 6. Contract API (logical)

```python
AKB.add_node(type, id, payload)
AKB.add_relationship(type, source_type, source_id, target_type, target_id)
AKB.get_node(type, id)
AKB.relationships_from(type, id, rel_type=None)
AKB.relationships_to(type, id, rel_type=None)
AKB.evidence_for_edge(edge_id)
AKB.trace_evidence(evidence_id)
AKB.trace_production_decision(decision_id)
AKB.trace_edge_to_datasets(edge_id)
```

## 7. Physical Storage (non-normative)

Initial implementation may use an in-memory stdlib graph. DuckDB is a
future physical adapter. Do not bake DuckDB semantics into ontology.

## 8. Acceptance Criteria

- node types recognized
- relationship types recognized
- Edge → Evidence is 1:N
- Evidence → Candidate → Experiment trace works
- ProductionDecision trace works
- Edge → Dataset trace works
- orphan ACTIVE Edge rejected
- tests prove query guarantees
