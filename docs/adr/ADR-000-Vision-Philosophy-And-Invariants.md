# ADR-000: Vision, Philosophy, and Invariants

- **Layer:** 0 (Constitution)
- **Status:** Draft
- **Date:** 2026-07-29

## Context

A long-lived, autonomous research system requires a foundational "North Star" to prevent architectural drift. This ADR codifies the supreme vision, philosophy, and unbreakable rules of AlphaOS. It exists so every future decision—technical or organizational—can be traced back to a stable reference.

## Decision

We adopt the following as the supreme law of the AlphaOS ecosystem.

### Vision

AlphaOS is an **autonomous, perpetually operating, self-evolving quantitative research operating system**. Its purpose is to systematically transform raw market data into a deep, auditable, ever-growing **Alpha Knowledge Base (AKB)**.

AlphaOS is not software for trading. AlphaOS is an operating system that *produces knowledge*, which software (the Production Engine) may then consume for trading.

### Philosophy

1. **The AKB is the OS.** The Alpha Knowledge Base is the single source of truth. All engines are stateless clients that query or mutate the AKB.
2. **Evidence is Law.** Production decisions are deterministic queries against the AKB. Nothing unvalidated is acted upon.
3. **The System is the Scientist.** Research is automated. The human role is strategic guidance and audit, not manual analysis.
4. **Alpha is Mortal; Research is Eternal.** Every edge decays. The permanent value is the continuous discovery pipeline, not any single edge.
5. **Radical Separation of Realms.** Research (complex, exploratory) and Production (simple, deterministic) are physically and logically separate.

### Non-Goals

AlphaOS is NOT:
- A discretionary trading bot or signal provider.
- A general-purpose backtesting platform for arbitrary ideas.
- An indicator library or charting application.
- A dashboard-first application (the dashboard is a window into the AKB).
- A place where humans hand-tune weights.

### Architectural Invariants (Unbreakable)

1. **Realm Purity:** Production never generates research. Research never executes live trades.
2. **Traceability:** Every production decision must reference the `EdgeID`(s) from the AKB that triggered it.
3. **Reproducibility:** Every Experiment must be perfectly replayable from its recorded configuration.
4. **Immutability:** Datasets and Evidence are never modified in place; change always produces a new versioned artifact.
5. **Permanent Identity:** Every core entity (Feature, Rule, Edge, Experiment) has a globally unique, permanent identifier.
6. **AST Supremacy:** All logical rules are represented as an Abstract Syntax Tree. String-parsed rules are forbidden.
7. **Lifecycle Mandate:** Every core domain entity has a managed lifecycle with legal transitions.
8. **Strict Versioning:** All key artifacts (data, features, rules, experiments) are strictly versioned.

## Consequences

- **Positive:** Extreme clarity of purpose; long-term architectural integrity; consistent decisions by humans and AIs alike.
- **Negative:** Strong constraints raise initial design cost and reduce short-term flexibility. Accepted deliberately.

## Alternatives Considered

- **Monolithic app:** Rejected — research instability would leak into production.
- **Informal vision (READMEs/tribal knowledge):** Rejected — insufficient for a system of this scale and lifespan.
- **No invariants:** Rejected — invariants are the enforcement mechanism for the philosophy.

## Migration Path

None. This is the founding document; all subsequent ADRs derive from it.
