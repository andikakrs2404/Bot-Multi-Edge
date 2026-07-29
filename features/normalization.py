"""
ADR-005 Normalization — cross-symbol percentile/zscore/minmax for every feature.

FeatureUpdateEvent → NormalizationEngine → NormalizedFeatureStore → NormalizedFeatureUpdateEvent.

V1: full recompute per FeatureUpdateEvent. O(N) per symbol per changed feature.
    Acceptable at ≤1k symbols. Trade/liq streams will push this higher.
V2: incremental normalization cache — precompute percentiles on timer, skip unchanged symbols.

Pitfall: percentile uses average-rank tie-breaking, not naive index + 1.
"""
from __future__ import annotations

import time
import statistics
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from market_data.events import Exchange
from market_data.event_bus import EventBus
from .registry import FeatureId
from .models import FeatureUpdateEvent, NormalizedFeature, NormalizedFeatureUpdateEvent

if TYPE_CHECKING:
    from .feature_store import FeatureStore

logger = logging.getLogger(__name__)


# ── strategy mapping ──

def _average_rank(raw_val: float, values: list[float]) -> float:
    """Fractional rank with average tie-breaking. Returns 1-based position."""
    if not values:
        return 1.0
    sorted_desc = sorted(values, reverse=True)
    try:
        first = next(i + 1 for i, v in enumerate(sorted_desc) if v == raw_val)
    except StopIteration:
        return float(len(values))  # below all
    tied = sum(1 for v in values if v == raw_val)
    return first + (tied - 1) / 2.0


def _z_to_percentile(z: float) -> float:
    """Standard normal CDF → percentile (0–100)."""
    dist = statistics.NormalDist(0, 1)
    return round(dist.cdf(z) * 100.0, 2)



#: Per-feature normalisation strategy.
#: "rank" | "zscore" | "minmax" | "minmax_inv" | "passthrough"
_NORM_STRATEGY: dict[FeatureId, str] = {
    FeatureId.VOLUME_1M:              "rank",
    FeatureId.OI:                     "rank",
    FeatureId.TRADE_COUNT_1M:         "rank",
    FeatureId.RSI_14_1M:              "rank",
    FeatureId.FUNDING_RATE:           "zscore",
    FeatureId.OI_CHANGE_1M:           "zscore",
    FeatureId.VOLUME_DELTA:           "zscore",
    FeatureId.FUNDING_ZSCORE:         "zscore",
    FeatureId.OI_1H_CHANGE:           "zscore",
    FeatureId.LIQUIDATION_IMBALANCE:  "zscore",
    FeatureId.BID_ASK_SPREAD:         "minmax_inv",
    FeatureId.VOLATILITY_1M:          "minmax_inv",
    FeatureId.PRICE:                  "passthrough",
    FeatureId.VWAP_1M:                "passthrough",
    FeatureId.HIGH_1M:                "passthrough",
    FeatureId.LOW_1M:                 "passthrough",
}


# ── engine ──

class NormalizationEngine:
    """Subscribes to FeatureUpdateEvent, cross-normalises, stores, notifies."""

    def __init__(self, bus: EventBus, store: FeatureStore) -> None:
        self._bus = bus
        self._store = store
        # Internal state: Exchange → symbol → feature_id → NormalizedFeature
        self._states: dict[Exchange, dict[str, dict[FeatureId, NormalizedFeature]]] = {}
        self._version: int = 0

    # ── lifecycle ──

    async def start(self) -> None:
        self._bus.subscribe(self._on_feature_update)
        logger.info("NormalizationEngine subscribed (%d strategies)", len(_NORM_STRATEGY))

    # ── public queries ──

    def get_normalised(
        self,
        exchange: Exchange,
        symbol: str,
        feature: FeatureId,
    ) -> NormalizedFeature | None:
        return self._states.get(exchange, {}).get(symbol, {}).get(feature)

    def get_symbol_state(
        self,
        exchange: Exchange,
        symbol: str,
    ) -> dict[FeatureId, NormalizedFeature] | None:
        return self._states.get(exchange, {}).get(symbol)

    def stats(self) -> dict:
        """Coverage snapshot."""
        sym_count = 0
        feat_count = 0
        for ex_states in self._states.values():
            sym_count += len(ex_states)
            for sym_state in ex_states.values():
                feat_count += len(sym_state)
        return {"symbols": sym_count, "features": feat_count, "version": self._version}

    def get_all_states(self) -> dict[Exchange, dict[str, dict[FeatureId, NormalizedFeature]]]:
        """Return a snapshot of the entire normalized feature state."""
        return self._states


    # ── normalisation dispatch ──

    async def _on_feature_update(self, event: object) -> None:
        if not isinstance(event, FeatureUpdateEvent):
            return

        ex_str = event.exchange
        try:
            exchange = Exchange(ex_str)
        except ValueError:
            return

        self._version += 1
        now = time.monotonic()
        changed: list[FeatureId] = []

        for fid in event.changed:
            strategy = _NORM_STRATEGY.get(fid)
            if strategy is None:
                continue
            raw = self._store.get_feature(exchange, event.symbol, fid, now)
            if raw is None:
                # raw stale — skip normalisation (keeps last known norm)
                continue

            if strategy == "passthrough":
                self._upsert(exchange, event.symbol, NormalizedFeature(
                    exchange=exchange.value, symbol=event.symbol,
                    feature=fid, value=raw.value,
                    percentile=50.0, zscore=0.0,
                    version=self._version, computed_at=now,
                ))
                changed.append(fid)
                continue

            # Gather all fresh raw values for this feature across symbols
            values: list[float] = []
            raw_map: dict[str, float] = {}
            for sym, state in self._store._states.get(exchange, {}).items():
                rf = state.features.get(fid)
                if rf is None:
                    continue
                if now - rf.computed_at > rf.ttl:
                    continue
                values.append(rf.value)
                raw_map[sym] = rf.value

            if len(values) < 2:
                continue  # not enough data yet

            nf = self._compute(exchange, event.symbol, fid, raw_map[event.symbol], values, strategy)
            self._upsert(exchange, event.symbol, nf)
            changed.append(fid)

        if changed:
            await self._bus.publish(NormalizedFeatureUpdateEvent(
                exchange=ex_str, symbol=event.symbol,
                changed=changed,
                version=self._version, computed_at=now,
            ))

    # ── helpers ──

    def _compute(self, exchange: Exchange, symbol: str, fid: FeatureId, raw_val: float, values: list[float],
                 strategy: str) -> NormalizedFeature:
        # ... (rest of the method body is the same, just the signature changes)
        match strategy:
            case "rank":
                avg_rank = _average_rank(raw_val, values)
                pct = (len(values) - avg_rank) / (len(values) - 1) * 100.0 if len(values) > 1 else 50.0
                mu = statistics.mean(values)
                sigma = statistics.stdev(values) if len(values) > 1 else 0.0
                z = (raw_val - mu) / sigma if sigma > 0 else 0.0
                return NormalizedFeature(
                    exchange=exchange.value, symbol=symbol,
                    feature=fid, value=raw_val,
                    percentile=round(pct, 2), zscore=round(z, 4),
                    version=self._version, computed_at=time.monotonic(),
                )
            # ... (zscore and minmax_inv cases similar)
            case "zscore":
                 mu = statistics.mean(values)
                 sigma = statistics.stdev(values) if len(values) > 1 else 0.0
                 z = (raw_val - mu) / sigma if sigma > 0 else 0.0
                 return NormalizedFeature(
                     exchange=exchange.value, symbol=symbol,
                     feature=fid, value=raw_val,
                     percentile=_z_to_percentile(z), zscore=round(z, 4),
                     version=self._version, computed_at=time.monotonic(),
                 )
            case "minmax_inv":
                vmin = min(values)
                vmax = max(values)
                norm = (raw_val - vmin) / (vmax - vmin) * 100.0 if vmax > vmin else 50.0
                pct = 100.0 - norm
                mu = statistics.mean(values)
                sigma = statistics.stdev(values) if len(values) > 1 else 0.0
                z = (raw_val - mu) / sigma if sigma > 0 else 0.0
                return NormalizedFeature(
                    exchange=exchange.value, symbol=symbol,
                    feature=fid, value=raw_val,
                    percentile=round(pct, 2), zscore=round(z, 4),
                    version=self._version, computed_at=time.monotonic(),
                )

        return NormalizedFeature(
            exchange=exchange.value, symbol=symbol,
            feature=fid, value=raw_val,
            percentile=50.0, zscore=0.0,
            version=self._version, computed_at=time.monotonic(),
        )

    def _upsert(self, exchange: Exchange, symbol: str, nf: NormalizedFeature) -> None:
        self._states.setdefault(exchange, {}).setdefault(symbol, {})[nf.feature] = nf
