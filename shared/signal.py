"""AlphaOS Signal Engine: Knowledge → Signal.

Consumes a Portfolio of ACTIVE edges + a live MarketSnapshot, evaluates
each edge's rule, and produces a deterministic SignalBatch.

No-signal convention: a rule that evaluates FALSE produces NO
DecisionSignal. An empty SignalBatch means neutral.
"""

from __future__ import annotations

from .contracts import (
    DecisionSignal,
    Edge,
    EdgeStatus,
    Portfolio,
    SignalBatch,
    SignalDirection,
    make_batch_id,
    make_signal_id,
)
from .registry import UnknownIdentityError
from .registries import EdgeRegistry, RuleRegistry
from .rules import FeatureValue, evaluate, parse
from .runtime import MarketSnapshot


class SignalEngineError(ValueError):
    """Signal engine invariant violation."""


class SignalEngine:
    def __init__(self, edge_registry: EdgeRegistry, rule_registry: RuleRegistry) -> None:
        self.edge_registry = edge_registry
        self.rule_registry = rule_registry

    def evaluate(self, portfolio: Portfolio, snapshot: MarketSnapshot) -> SignalBatch:
        signals = []
        for allocation in portfolio.allocations:
            try:
                edge = self.edge_registry.get(allocation.edge_id)
            except UnknownIdentityError:
                raise SignalEngineError(
                    f"edge not found: {allocation.edge_id}") from None
            if edge.status != EdgeStatus.ACTIVE:
                raise SignalEngineError(
                    f"edge must be ACTIVE: {allocation.edge_id}")
            try:
                rule = self.rule_registry.get(edge.rule_id)
            except UnknownIdentityError:
                raise SignalEngineError(f"rule not found: {edge.rule_id}") from None
            ast = parse(rule.ast)
            ctx = self._build_context(snapshot)
            try:
                triggered = evaluate(ast, ctx)
            except KeyError as exc:
                raise SignalEngineError(
                    f"feature missing from snapshot: {exc.args[0]}") from None
            if triggered:
                signals.append(self._build_signal(
                    edge, allocation.direction, portfolio, snapshot))
        signals.sort(key=lambda s: s.edge_id)
        return SignalBatch(
            batch_id=make_batch_id(
                portfolio.portfolio_id, snapshot.snapshot_id,
                tuple(s.signal_id for s in signals)),
            portfolio_id=portfolio.portfolio_id,
            market_snapshot_id=snapshot.snapshot_id,
            signals=tuple(signals),
        )

    def _build_context(self, snapshot: MarketSnapshot) -> dict[str, FeatureValue]:
        return {name: FeatureValue(value=value)
                for name, value in snapshot.feature_values.items()}

    def _build_signal(self, edge: Edge, direction: SignalDirection,
                      portfolio: Portfolio, snapshot: MarketSnapshot) -> DecisionSignal:
        signal_id = make_signal_id(
            edge.edge_id, portfolio.portfolio_id, snapshot.snapshot_id,
            snapshot.symbol, direction)
        return DecisionSignal(
            signal_id=signal_id,
            edge_id=edge.edge_id,
            rule_id=edge.rule_id,
            experiment_id=edge.experiment_id,
            portfolio_id=portfolio.portfolio_id,
            symbol=snapshot.symbol,
            market_snapshot_id=snapshot.snapshot_id,
            direction=direction,
            confidence=1.0,
        )
