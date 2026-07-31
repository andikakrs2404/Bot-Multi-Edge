# ADR-001A: Decision Record Protocol

- **Layer:** 0 (Constitution)
- **Status:** Draft
- **Date:** 2026-07-29
- **Depends On:** ADR-001

## Context

Architecture decisions compound. Without a uniform record format, ADRs become inconsistent, unverifiable, and impossible to audit over a 10+ year horizon. This ADR fixes the mandatory structure and governance rules for ALL current and future ADRs.

## Decision

### ADR Status Lifecycle

Only four statuses exist:

```text
DRAFT → PROPOSED → RATIFIED → SUPERSEDED
```

- **DRAFT:** may change freely.
- **PROPOSED:** under formal review; no substantive edits without review notes.
- **RATIFIED:** immutable. Never edited again.
- **SUPERSEDED:** replaced by a newer ADR; retained as history.

**RATIFIED ADRs are never edited.** Any change, however small, requires a new ADR that supersedes the old one. This preserves the decision history intact.

### Mandatory ADR Structure

Every ADR MUST contain:

1. **Title:** `ADR-XXX: Descriptive Title`
2. **Metadata:** Layer, Status, Date, Depends On
3. **Context:** the problem and why the decision is needed now
4. **Decision:** the unambiguous decision itself
5. **Consequences:** positive AND negative
6. **Alternatives Considered:** what was evaluated and rejected, and why
7. **Migration Path:** how to move from a superseded decision (or "None")

### Constitutional Freeze Protocol

- Layer 0–1 ADRs are ratified TOGETHER as one package (Big-Bang ratification), never individually.
- A freeze package records: version, date, git commit, reviewer, list of included ADRs, and an **Architectural Hash**.
- **Architectural Hash:** `SHA256` over the concatenation of all ratified ADR files. Every Experiment records the `constitution_hash` it ran under.

### Constitutional Scope Lock

During a freeze, NO new domain concepts may be added. Only clarity fixes, contradiction repairs, and wording corrections are permitted.

## Consequences

- **Positive:** Uniform quality; verifiable decision history; reproducibility across decades; linter-friendly ADRs.
- **Negative:** Ceremony overhead for changes. Accepted.

## Alternatives Considered

- **Free-form ADRs:** Rejected — quality drifts.
- **Per-ADR ratification:** Rejected — cross-ADR consistency is only guaranteed by package ratification.

## Migration Path

None for v1.0.
