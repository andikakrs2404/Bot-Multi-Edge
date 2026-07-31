# Specification: Registry Model

Derived from: ADR-005 (Registry Model), ADR-002 (Domain Ontology), ADR-004 (Dataset Versioning)
Constitution: be37bf97... (Freeze v1.0, 2026-07-29)

Status: Draft (v0.1)

## 1. Purpose

The Registry is the **source of truth for domain entity definitions**. No entity (Feature, Label, Rule, Dataset, Edge) may be used by an Experiment or engine before it is registered. Identity comes from the Registry, not from consuming code.

## 2. Registry Entry

Every registry entry has the following fields:

| Field | Type | Notes |
| --- | --- | --- |
| `entity_id` | str | permanent identity; never changes (ADR-002 axiom 5) |
| `version` | int | per-entity version counter |
| `status` | enum | see §3 |
| `created_at` | datetime | UTC |
| `created_by` | str | actor: `system` \| `human:<name>` |
| `superseded_by` | str \| null | entity_id of the replacement (or null) |
| `constitution_hash` | str | hash under which this entry was registered |
| `registry_version` | int | global per-registry counter, incremented on every mutation |

The `registry_version` is the value Experiments reference:

```yaml
feature_registry_version: 12
label_registry_version: 4
```

## 3. Registry Status

```text
REGISTERED → ACTIVE → SUPERSEDED
                 │
                 ▼
              ARCHIVED
```

- **REGISTERED:** entry exists, not yet in use.
- **ACTIVE:** current, usable definition (exactly one ACTIVE entry per identity).
- **SUPERSEDED:** replaced by a newer entry; retained as history.
- **ARCHIVED:** no longer usable, not superseded (e.g. retired); retained as history.

## 4. Version Rules

1. **Identity is permanent.** Evolution of a definition creates a NEW `entity_id` (ADR-005). The `version` field tracks the *registration lifecycle* of one identity, not definition changes.
2. **Immutability.** Once ACTIVE, an entry's definition fields never change.
3. **One ACTIVE per identity.** Registering a new ACTIVE entry for the same `entity_id` is an error; the existing one must first be SUPERSEDED or ARCHIVED.

## 5. Supersession Rules

1. `supersede(entity_id, reason)` marks the ACTIVE entry SUPERSEDED and sets `superseded_by` to the successor id.
2. Successor entries MUST reference their predecessor via `lineage` (ADR-002 `derives` relationship).
3. Superseded entries remain queryable forever (history is immutable).

## 6. Lookup Semantics

| Call | Semantics |
| --- | --- |
| `get(entity_id)` | the ACTIVE entry for the identity |
| `get_version(entity_id, version)` | a specific historical version |
| `latest(entity_id)` | alias of `get` |
| `history(entity_id)` | all versions, oldest → newest |
| `all_active()` | all ACTIVE entries in the registry |
| `resolve(name)` | ACTIVE entry by canonical name (identity) |

## 7. Validation

`validate(entry)` enforces:
- `entity_id` matches canonical naming (per `docs/standards/`)
- required definition fields non-empty
- `constitution_hash` matches the frozen constitution
- no duplicate ACTIVE identity
- status transitions are legal (ADR-002A)

## 8. Kinds

All registries share this kernel. Concrete kinds:

| Registry | Entity kind | Identity prefix |
| --- | --- | --- |
| FeatureRegistry | `feature` \| `label` | `FEAT-` / `LAB-` |
| RuleRegistry | `rule` | `RULE-` |
| DatasetRegistry | `dataset` | `DS-` |
| EdgeRegistry | `edge` | `EDGE-` |
