"""
ADR-006 Breadth Engine.

Computes market-wide breadth indicators from normalized features.

NormalizedFeatureUpdateEvent → BreadthEngine → MarketBreadth (event)
"""
from __future__ import annotations
import time
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .models import NormalizedFeatureUpdateEvent, MarketBreadth
from .registry import FeatureId

if TYPE_CHECKING:
    from market_data.event_bus import EventBus
    from .normalization import NormalizationEngine


logger = logging.getLogger(__name__)


class BreadthEngine:
    def __init__(self, bus: EventBus, norm: NormalizationEngine):
        self._bus = bus
        self._norm = norm
        self._version = 0

    async def start(self):
        # Subscribes to the output of the NormalizationEngine
        self._bus.subscribe(self._on_normalized_feature_update)
        logger.info("BreadthEngine subscribed to NormalizedFeatureUpdateEvent")

    async def _on_normalized_feature_update(self, event: object) -> None:
        if not isinstance(event, NormalizedFeatureUpdateEvent):
            return

        # V1: Recompute all breadth metrics on any update.
        # V2: Could be optimized to update only relevant metrics.
        self._version += 1
        now = time.monotonic()

        all_states = self._norm.get_all_states() # Needs to be implemented in NormalizationEngine
        if not all_states:
            return

        # 1. Advance/Decline Ratio (proxy: price > vwap_1m)
        advancing = 0
        declining = 0
        for ex_states in all_states.values():
            for sym_state in ex_states.values():
                price_nf = sym_state.get(FeatureId.PRICE)
                vwap_nf = sym_state.get(FeatureId.VWAP_1M)
                if price_nf and vwap_nf:
                    if price_nf.value > vwap_nf.value:
                        advancing += 1
                    else:
                        declining += 1
        ad_ratio = advancing / (advancing + declining) if (advancing + declining) > 0 else 0.5

        # 2. Momentum Breadth (RSI > 60)
        strong_momentum = 0
        total_with_rsi = 0
        for ex_states in all_states.values():
            for sym_state in ex_states.values():
                rsi_nf = sym_state.get(FeatureId.RSI_14_1M)
                if rsi_nf:
                    total_with_rsi += 1
                    if rsi_nf.value > 60:
                        strong_momentum += 1
        momentum_breadth = strong_momentum / total_with_rsi if total_with_rsi > 0 else 0.0

        # 3. Volume Participation (z-score > 1)
        high_volume = 0
        total_with_vol = 0
        for ex_states in all_states.values():
            for sym_state in ex_states.values():
                vol_nf = sym_state.get(FeatureId.VOLUME_1M)
                if vol_nf:
                    total_with_vol += 1
                    if vol_nf.zscore > 1.0:
                        high_volume += 1
        volume_participation = high_volume / total_with_vol if total_with_vol > 0 else 0.0

        # 4. OI Participation (z-score > 1)
        high_oi = 0
        total_with_oi = 0
        for ex_states in all_states.values():
            for sym_state in ex_states.values():
                oi_nf = sym_state.get(FeatureId.OI)
                if oi_nf:
                    total_with_oi += 1
                    if oi_nf.zscore > 1.0:
                        high_oi += 1
        oi_participation = high_oi / total_with_oi if total_with_oi > 0 else 0.0

        # Publish the market breadth summary
        breadth_event = MarketBreadth(
            timestamp=now,
            ad_ratio_1m=round(ad_ratio, 4),
            momentum_breadth_rsi14=round(momentum_breadth, 4),
            volume_participation=round(volume_participation, 4),
            oi_participation=round(oi_participation, 4),
            version=self._version
        )
        await self._bus.publish(breadth_event)
