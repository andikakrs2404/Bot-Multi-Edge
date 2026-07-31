# ADR-005: Registry Model (Feature & Label)

- **Layer:** 1 (Domain & Contracts)
- **Status:** Ratified
- **Date:** 2026-07-29
- **Depends On:** ADR-004

## Context

Features and Labels are the raw material of all research. If their definitions are scattered across code or ad hoc notebooks, the same name can mean different things in different experiments — destroying comparability and reproducibility. This ADR fixes a single Registry Model for both, treating Feature and Label as the same kind of registered entity with a type discriminator.

## Decision

### Registry Model

One registry concept, two kinds:

- **Feature Registry** — entities of kind `feature` (derived properties of market state).
- **Label Registry** — entities of kind `label` (future outcomes, research-only).

Both share the same record structure and governance.

### Record Structure (field-level spec in `docs/specifications/`)

Every registered Feature/Label has:
- `id` (globally unique, permanent — the name IS the identity),
- `kind` (`feature` | `label`),
- `formula` (canonical definition; for Features: an AST expression over base inputs; for Labels: the outcome definition),
- `version` (definition evolution creates a new id, not a version bump — see below),
- `category`, `owner`, `status`, `created_at`, `lineage` (derived_from references).

### Identity & Evolution

1. **Identity is permanent** (Axiom 5, ADR-002): the id never changes.
2. **Evolution = new entity:** any change to a definition creates a NEW Feature/Label with a new id. Old ids remain valid history.
3. **Lineage:** `derived_from` relationships form the feature family graph in the AKB.

### Governance

- All Features consumed by experiments MUST be registered before use.
- Unregistered features are forbidden in experiments (linter-enforced).
- Labels are forbidden in Production by construction (trust model, ADR-000B).

## Consequences

- **Positive:** One definition, one identity; cross-experiment comparability; family/lineage analysis possible; production cannot accidentally consume labels.
- **Negative:** Registering every feature adds ceremony. Accepted.

## Alternatives Considered

- **Separate registries with different rules:** Rejected — they are the same concept; divergence would be artificial.
- **No registry:** Rejected — name collisions and definition drift.

## Migration Path

None for v1.0.
