"""
ADR-007 Ranking Engine.

Consumes normalized features and market breadth to produce a ranked list of symbols.
"""
from __future__ import annotations
import time
import logging
from typing import TYPE_CHECKING

from .models import (
    NormalizedFeatureUpdateEvent, MarketBreadth, RankedSymbol
)
from .registry import FeatureId

if TYPE_CHECKING:
    from market_data.event_bus import EventBus
    from .normalization import NormalizationEngine

logger = logging.getLogger(__name__)


# ── Ranking Formula V1 Weights ──
WEIGHTS = {
    "rsi": 0.35,
    "volume": 0.25,
    "oi": 0.25,
    "breadth": 0.15,
}

class RankingStore:
    """In-memory store for ranked symbols."""
    def __init__(self, top_n: int = 100):
        self._top_n = top_n
        self._rankings: list[RankedSymbol] = []
        self._by_symbol: dict[tuple[str, str], RankedSymbol] = {}
        self._version: int = 0

    def update(self, ranked_symbols: list[RankedSymbol]):
        self._version += 1
        # Sort by score descending and assign rank
        ranked_symbols.sort(key=lambda x: x.score, reverse=True)
        for i, rs in enumerate(ranked_symbols):
            rs.rank = i + 1
        
        self._rankings = ranked_symbols[:self._top_n]
        self._by_symbol = {(rs.exchange, rs.symbol): rs for rs in self._rankings}
        logger.info(f"RankingStore updated with {len(self._rankings)} symbols (v{self._version})")

    def get(self, exchange: str, symbol: str) -> RankedSymbol | None:
        return self._by_symbol.get((exchange, symbol))

    def get_top_n(self) -> list[RankedSymbol]:
        return self._rankings

    def stats(self) -> dict:
        return {
            "ranked_symbols": len(self._rankings),
            "version": self._version,
        }


class RankingEngine:
    def __init__(self, bus: EventBus, norm: NormalizationEngine, store: RankingStore):
        self._bus = bus
        self._norm = norm
        self._store = store
        self._last_breadth: MarketBreadth | None = None
        self._version: int = 0

    async def start(self):
        self._bus.subscribe(self._on_normalized_update)
        self._bus.subscribe(self._on_breadth_update)
        logger.info("RankingEngine subscribed to normalized and breadth events")

    async def _on_breadth_update(self, event: object):
        if isinstance(event, MarketBreadth):
            self._last_breadth = event
            # On new breadth, re-rank everything
            await self._re_rank_all()

    async def _on_normalized_update(self, event: object):
        if isinstance(event, NormalizedFeatureUpdateEvent):
            # V1: Re-rank everything on any update.
            # V2: Could be optimized to only re-rank the affected symbol and its neighbours.
            await self._re_rank_all()

    async def _re_rank_all(self):
        self._version += 1
        now = time.monotonic()
        
        all_norm_states = self._norm.get_all_states()
        if not all_norm_states:
            return

        ranked_symbols = []
        for exchange, ex_states in all_norm_states.items():
            for symbol, norm_state in ex_states.items():
                score, components = self._compute_score(norm_state)
                if score is not None:
                    ranked_symbols.append(RankedSymbol(
                        exchange=exchange.value,
                        symbol=symbol,
                        score=score,
                        rank=0, # Will be set in store
                        **components,
                        version=self._version,
                        computed_at=now,
                    ))
        
        self._store.update(ranked_symbols)

    def _compute_score(self, norm_state: dict[FeatureId, NormalizedFeature]) -> tuple[float, dict] | tuple[None, None]:
        rsi_nf = norm_state.get(FeatureId.RSI_14_1M)
        vol_nf = norm_state.get(FeatureId.VOLUME_1M)
        oi_nf = norm_state.get(FeatureId.OI)

        if not all([rsi_nf, vol_nf, oi_nf]):
            return None, None # Not enough features to rank

        # Component scores are based on percentiles (0-100)
        momentum_score = rsi_nf.percentile
        volume_score = vol_nf.percentile
        oi_score = oi_nf.percentile
        
        # Breadth multiplier (0.7 to 1.15)
        breadth_composite = 0.0
        if self._last_breadth:
            # Simple average of breadth metrics
            breadth_composite = (
                self._last_breadth.ad_ratio_1m +
                self._last_breadth.momentum_breadth_rsi14 +
                self._last_breadth.volume_participation +
                self._last_breadth.oi_participation
            ) / 4.0 * 100 # scale to 0-100

        breadth_score = breadth_composite # For explainability
        
        base_score = (
            momentum_score * WEIGHTS["rsi"] +
            volume_score * WEIGHTS["volume"] +
            oi_score * WEIGHTS["oi"]
        )
        
        # Apply breadth as a simple weighted factor for V1
        final_score = base_score * (1 - WEIGHTS["breadth"]) + breadth_score * WEIGHTS["breadth"]

        components = {
            "momentum_score": round(momentum_score, 2),
            "volume_score": round(volume_score, 2),
            "oi_score": round(oi_score, 2),
            "breadth_score": round(breadth_score, 2),
        }
        
        return round(final_score, 2), components
