# ADR-001B: Architectural Quality Attributes

- **Layer:** 0 (Constitution)
- **Status:** Draft
- **Date:** 2026-07-29
- **Depends On:** ADR-001A

## Context

When two designs are both "correct", the system still needs a deterministic way to choose. Without explicit priorities, teams optimize for whatever is easiest to build now — usually performance or convenience — at the expense of long-term properties. This ADR fixes the quality attribute hierarchy used to arbitrate ALL design tradeoffs.

## Decision

Quality attributes are ordered by priority. A lower-priority attribute may NEVER be satisfied at the expense of a higher-priority one.

| Priority | Attribute | Meaning |
| --- | --- | --- |
| 1 | Reproducibility | Same inputs + same config ⇒ same outputs, forever. |
| 2 | Auditability | Every result and decision traceable to its provenance. |
| 3 | Determinism | Production behavior fully determined by AKB + market input. |
| 4 | Correctness | Results match the domain contracts exactly. |
| 5 | Extensibility | Adding features, labels, rules, engines does not require rework. |
| 6 | Performance | Throughput/latency of pipelines and engines. |
| 7 | Developer Convenience | Ease of writing and debugging code. |

**Arbitration rule:** a proposal that improves Performance but harms Reproducibility is REJECTED. A proposal that improves Developer Convenience but harms Auditability is REJECTED. Only proposals that preserve or improve higher-priority attributes are eligible.

## Consequences

- **Positive:** Objective, defensible design arbitration; prevents "easy-now, painful-later" decisions.
- **Negative:** Sometimes forces more rigorous (slower to write) solutions. Accepted.

## Alternatives Considered

- **Equal weighting:** Rejected — unresolvable conflicts.
- **Performance-first:** Rejected — destroys the research mission (reproducibility).

## Migration Path

None for v1.0. Attribute reordering requires a superseding ADR.
