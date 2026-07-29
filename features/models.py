"""
Data models for the feature pipeline (ADR-004, ADR-005, ADR-006).

Events, raw/normalized features, and market breadth summaries.
"""
from __future__ import annotations
import time
from dataclasses import dataclass, field
from .registry import FeatureId


# ── ADR-004 Raw Features ──

@dataclass(slots=True)
class RawFeature:
    """A single raw feature value at a point in time."""
    feature: FeatureId
    value: float
    ttl: int = 60  # seconds
    computed_at: float = field(default_factory=time.time)

@dataclass(slots=True)
class SymbolFeatureState:
    """All raw features for one symbol."""
    exchange: str
    symbol: str
    features: dict[FeatureId, RawFeature] = field(default_factory=dict)
    def update(self, feature: RawFeature) -> None:
        self.features[feature.feature] = feature

@dataclass(slots=True)
class FeatureUpdateEvent:
    """Notification of a raw feature state change."""
    exchange: str
    symbol: str
    changed: list[FeatureId]
    version: int
    computed_at: float


# ── ADR-005 Normalized Features ──

@dataclass(slots=True)
class NormalizedFeature:
    """One normalised feature value for one symbol."""
    exchange: str
    symbol: str
    feature: FeatureId
    value: float
    percentile: float
    zscore: float
    version: int
    computed_at: float

@dataclass(slots=True)
class NormalizedFeatureUpdateEvent:
    """Notification of a normalized feature state change."""
    exchange: str
    symbol: str
    changed: list[FeatureId]
    version: int
    computed_at: float


# ── ADR-006 Market Breadth ──

@dataclass(slots=True)
class MarketBreadth:
    """Snapshot of market-wide conditions."""
    timestamp: float
    ad_ratio_1m: float
    momentum_breadth_rsi14: float
    volume_participation: float
    oi_participation: float
    version: int = 0


# ── ADR-007 Ranking ──

@dataclass(slots=True)
class RankedSymbol:
    """Final ranking output for one symbol."""
    exchange: str
    symbol: str

    score: float               # final composite score 0-100
    rank: int                  # current rank position 1..N

    # Explainability components
    momentum_score: float      # RSI / trend component
    volume_score: float        # participation component
    oi_score: float            # open-interest component
    breadth_score: float       # market breadth boost/penalty

    version: int
    computed_at: float

