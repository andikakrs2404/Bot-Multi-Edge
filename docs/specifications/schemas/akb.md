# Specification: AKB Schema (DuckDB v1.0)

Derived from: ADR-009 (AKB Representation), ADR-008 (Evidence Model)

Status: Draft (v0.1) — storage representation of the knowledge graph.

## Storage Model

Immutable Parquet artifacts (content-addressed) + DuckDB indexes/views over them.

## Tables

### registries
| column | type | notes |
| --- | --- | --- |
| kind | VARCHAR | dataset \| feature \| label \| rule |
| id | VARCHAR | permanent id |
| version | INTEGER | |
| manifest | JSON | definition, formula, lineage |
| status | VARCHAR | lifecycle status |
| created_at | TIMESTAMP | |

### experiments
| column | type |
| --- | --- |
| experiment_id | VARCHAR (PK) |
| config | JSON (full ExperimentConfig) |
| status | VARCHAR |
| started_at / finished_at | TIMESTAMP |
| constitution_hash | VARCHAR |

### evidence_bundles
| column | type |
| --- | --- |
| bundle_id | VARCHAR (PK) |
| experiment_id | VARCHAR (FK) |
| candidate_id | VARCHAR |
| metrics | JSON |
| reports_refs | JSON (artifact hashes) |
| created_at | TIMESTAMP |

### edges
| column | type |
| --- | --- |
| edge_id | VARCHAR (PK) |
| rule_id | VARCHAR |
| experiment_id | VARCHAR (FK) |
| status | VARCHAR |
| lifecycle_history | JSON (transition log) |
| health_score | DOUBLE |
| created_at / retired_at | TIMESTAMP |

### portfolios
| column | type |
| --- | --- |
| portfolio_id | VARCHAR (PK) |
| objective | VARCHAR |
| status | VARCHAR |
| allocations | JSON |
| risk_policy | JSON |

### production_decisions
| column | type |
| --- | --- |
| decision_id | VARCHAR (PK) |
| ts | TIMESTAMP |
| portfolio_id | VARCHAR (FK) |
| triggered_edges | JSON |
| decision | VARCHAR |
| confidence | DOUBLE |
| execution_result | JSON |

### knowledge_graph (relationship edges)
| column | type |
| --- | --- |
| rel_id | VARCHAR (PK) |
| source_type / source_id | VARCHAR |
| target_type / target_id | VARCHAR |
| rel_type | VARCHAR (derives, produces, supported_by, supersedes, allocated_to, drives, uses, tests) |
| created_by_experiment | VARCHAR |
| created_at | TIMESTAMP |

## Access Rules

- Research: append-only writes via engine artifacts.
- Production: read-only views on `edges` (status ACTIVE), `portfolios`, `production_decisions`.
