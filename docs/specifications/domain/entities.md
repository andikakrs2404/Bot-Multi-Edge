# Specification: Domain Entities (Field-Level)

Derived from: ADR-002 (Domain Ontology), ADR-002A (Domain Lifecycles)

Status: Draft (v0.1)

## EdgeRecord

```yaml
edge_id: EDGE-<hash>          # permanent identity
rule_id: "sha256..."          # canonical AST hash
experiment_id: EXP-...
status: VALIDATED            # lifecycle per ADR-002A
version: 1
birth_date: ...
activation_date: null
last_seen: ...
health_score: null           # set while MONITORED
confidence: null
usage_count: 0
live_pf: null
paper_pf: null
retirement_reason: null
```

## PortfolioRecord

```yaml
portfolio_id: PF-...
objective: max_sharpe | min_dd | market_neutral | momentum
status: DRAFT                # lifecycle per ADR-002A
allocations:                 # only ACTIVE edges allowed
  - edge_id: EDGE-...
    weight: 0.25
risk_policy: {...}
rebalance_policy: {...}
```

## ProductionDecisionRecord

```yaml
decision_id: DEC-...
ts: ...
portfolio_id: PF-...
triggered_edges: [EDGE-..., ...]
market_snapshot_ref: "sha256..."
risk_snapshot_ref: "sha256..."
decision: BUY | SELL | HOLD | SKIP
confidence: 0.87
execution_result: {status, order_id, filled_qty, avg_price}
```

## Lifecycle Transition Log

Every lifecycle transition is recorded:

```yaml
entity_type: edge
entity_id: EDGE-...
from: VALIDATED
to: ACTIVE
actor: research_engine | human_operator
ts: ...
reason: "approved by review"
```
