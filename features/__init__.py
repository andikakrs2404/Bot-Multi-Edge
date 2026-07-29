"""
This package contains the core components of the feature store,
as defined in ADR-004.
"""
from .registry import (
    FeatureId,
    FeatureDefinition,
    FEATURE_REGISTRY,
)

from .models import (
    RawFeature,
    SymbolFeatureState,
    FeatureUpdateEvent,
)

from .windows import (
    WindowManager,
    SymbolWindowState,
    DefaultWindowManager,
)

from .handlers import (
    FeatureHandler,
    TickerHandler,
    TradeHandler,
    OpenInterestHandler,
    FundingHandler,
    CandleHandler,
    LiquidationHandler,
)
from .feature_store import FeatureStore
from .normalization import NormalizationEngine, NormalizedFeature, NormalizedFeatureUpdateEvent
from .breadth import BreadthEngine, MarketBreadth

__all__ = [
    "FeatureId",
    "FeatureDefinition",
    "FEATURE_REGISTRY",
    "RawFeature",
    "SymbolFeatureState",
    "FeatureUpdateEvent",
    "WindowManager",
    "SymbolWindowState",
    "DefaultWindowManager",
    "FeatureHandler",
    "TickerHandler",
    "TradeHandler",
    "OpenInterestHandler",
    "FeatureStore",
]
