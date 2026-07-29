"""Feature identity — enum + definitions + registry.

This module is the single source of truth for all features in the pipeline.
Feature handlers, TTL, windows — everything is driven by this registry.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class FeatureId(StrEnum):
    """Unique feature identifiers. Every feature in the pipeline lives here."""

    PRICE = "price"
    VOLUME_1M = "volume_1m"
    VWAP_1M = "vwap_1m"
    OI = "oi"
    OI_CHANGE_1M = "oi_change_1m"
    FUNDING_RATE = "funding_rate"
    FUNDING_ZSCORE = "funding_zscore"
    TRADE_COUNT_1M = "trade_count_1m"
    BID_ASK_SPREAD = "bid_ask_spread"
    VOLUME_DELTA = "volume_delta"
    HIGH_1M = "high_1m"
    LOW_1M = "low_1m"
    VOLATILITY_1M = "volatility_1m"
    OI_1H_CHANGE = "oi_1h_change"
    LIQUIDATION_IMBALANCE = "liquidation_imbalance"
    RSI_14_1M = "rsi_14_1m"


_HandlerFn = Callable[..., list[tuple[FeatureId, float]]]


@dataclass(slots=True, frozen=True)
class FeatureDefinition:
    """Immutable definition of one feature in the pipeline."""

    id: FeatureId
    ttl: int
    description: str
    handler_id: str = ""
    depends_on: tuple[FeatureId, ...] = ()
    version: int = 1


# ── Registry — single dict, single source of truth ──

FEATURE_REGISTRY: dict[FeatureId, FeatureDefinition] = {
    # Ticker-derived
    FeatureId.PRICE: FeatureDefinition(id=FeatureId.PRICE, ttl=5, description="Last traded price", handler_id="ticker"),
    FeatureId.VOLUME_1M: FeatureDefinition(id=FeatureId.VOLUME_1M, ttl=60, description="Volume last 1m", handler_id="ticker"),
    FeatureId.BID_ASK_SPREAD: FeatureDefinition(id=FeatureId.BID_ASK_SPREAD, ttl=5, description="(ask-bid)/mid", handler_id="ticker"),
    FeatureId.VOLUME_DELTA: FeatureDefinition(id=FeatureId.VOLUME_DELTA, ttl=60, description="Buy vol - sell vol", handler_id="ticker"),

    # Trade-derived
    FeatureId.VWAP_1M: FeatureDefinition(id=FeatureId.VWAP_1M, ttl=60, description="VWAP 1m", handler_id="trade"),
    FeatureId.TRADE_COUNT_1M: FeatureDefinition(id=FeatureId.TRADE_COUNT_1M, ttl=60, description="Trade count 1m", handler_id="trade"),

    # Candle-derived
    FeatureId.HIGH_1M: FeatureDefinition(id=FeatureId.HIGH_1M, ttl=60, description="1m high", handler_id="candle"),
    FeatureId.LOW_1M: FeatureDefinition(id=FeatureId.LOW_1M, ttl=60, description="1m low", handler_id="candle"),
    FeatureId.VOLATILITY_1M: FeatureDefinition(id=FeatureId.VOLATILITY_1M, ttl=60, description="(high-low)/close 1m", handler_id="candle"),
    FeatureId.RSI_14_1M: FeatureDefinition(id=FeatureId.RSI_14_1M, ttl=120, description="RSI 14 from 1m candles", handler_id="candle"),

    # OI-derived
    FeatureId.OI: FeatureDefinition(id=FeatureId.OI, ttl=60, description="Open interest", handler_id="open_interest"),
    FeatureId.OI_CHANGE_1M: FeatureDefinition(
        id=FeatureId.OI_CHANGE_1M, ttl=65, description="OI change % 1m", handler_id="open_interest",
        depends_on=(FeatureId.OI,),
    ),
    FeatureId.OI_1H_CHANGE: FeatureDefinition(
        id=FeatureId.OI_1H_CHANGE, ttl=3600, description="OI change % 1h", handler_id="open_interest",
        depends_on=(FeatureId.OI,),
    ),

    # Funding-derived
    FeatureId.FUNDING_RATE: FeatureDefinition(id=FeatureId.FUNDING_RATE, ttl=480, description="Funding rate", handler_id="funding"),
    FeatureId.FUNDING_ZSCORE: FeatureDefinition(
        id=FeatureId.FUNDING_ZSCORE, ttl=600, description="Z-score vs 8h", handler_id="funding",
        depends_on=(FeatureId.FUNDING_RATE,),
    ),

    # Liquidation-derived
    FeatureId.LIQUIDATION_IMBALANCE: FeatureDefinition(
        id=FeatureId.LIQUIDATION_IMBALANCE, ttl=60, description="Long/short liq imbalance", handler_id="liquidation"
    ),
}


# ── Fast name → definition lookup ──

def get_feature(id: FeatureId) -> FeatureDefinition:
    return FEATURE_REGISTRY[id]


def list_features() -> list[FeatureDefinition]:
    return list(FEATURE_REGISTRY.values())
