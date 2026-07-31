# ADR-000A: Ubiquitous Language

- **Layer:** 0 (Constitution)
- **Status:** Ratified
- **Date:** 2026-07-29
- **Depends On:** ADR-000

## Context

Ambiguity is the root of architectural rot. In a system where research, production, documentation, and AI agents must cooperate for years, every term must have exactly one meaning. This ADR fixes the canonical vocabulary of AlphaOS (Domain-Driven Design "ubiquitous language"). New terms may only be introduced via ADR amendment.

## Decision

The following terms are canonical. All ADRs, specifications, code identifiers, and documentation MUST use them with these meanings. Synonyms are forbidden.

| Term | Definition |
| --- | --- |
| **Observation** | A raw measurement of market state at a point in time (price, volume, OI, funding). |
| **Feature** | A derived, measurable property of market state, computed from Observations. Immutable identity. |
| **Label** | A future outcome used only during research to evaluate Features or Rules. Never available in production. |
| **Rule** | A logical expression (AST) over Features that evaluates to true/false. |
| **Candidate** | A Rule proposed for evaluation, owned by exactly one Experiment. |
| **Experiment** | A reproducible execution of the research protocol over a specific Dataset with a specific configuration. |
| **Evidence** | Statistical results produced by an Experiment that support or refute a Candidate. |
| **Edge** | A Candidate that has passed all validation stages and been promoted into the AKB as Knowledge. |
| **Knowledge** | The validated content of the AKB (Edges and their relationships). |
| **Portfolio** | A curated, risk-managed allocation over Active Edges. |
| **ProductionDecision** | An auditable action taken by the Production Engine, referencing a Portfolio. |
| **ResearchCycle** | A complete scheduled run of the research pipeline (trigger → discovery → validation → AKB update). |
| **Alpha Knowledge Base (AKB)** | The persistent representation of all domain Knowledge and its provenance graph. |
| **Realm** | One of the two top-level partitions of AlphaOS: Research or Production. |

## Consequences

- **Positive:** Every document and codebase speaks one language; cross-module miscommunication becomes impossible by construction.
- **Negative:** Introducing a genuinely new concept requires an ADR, adding ceremony. Accepted.

## Alternatives Considered

- **Per-module glossaries:** Rejected — they drift apart.
- **No glossary:** Rejected — ambiguity would compound over years.

## Migration Path

None for v1.0. New terms require a superseding ADR.
