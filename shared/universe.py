"""AlphaOS Universe Definition (ADR-003/004, spec raw-data-engine §4).

Universe is a reproducible artifact, never hardcoded in the engine.
Tier is dataset metadata (universe characteristic), not a feature.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from .validation import dataset_id_of


class Tier(str, Enum):
    A = "A"   # volume > 100M USDT/24h
    B = "B"   # 20M - 100M
    C = "C"   # 5M - 20M
    D = "D"   # < 5M


def tier_of(volume_usdt_24h: float) -> Tier:
    if volume_usdt_24h > 100e6:
        return Tier.A
    if volume_usdt_24h > 20e6:
        return Tier.B
    if volume_usdt_24h > 5e6:
        return Tier.C
    return Tier.D


# stablecoin pairs + leveraged tokens excluded from futures universe
EXCLUDED_SYMBOLS = {
    "USDCUSDT", "FDUSDUSDT", "TUSDUSDT", "USDPUSDT", "EURUSDT", "AEURUSDT",
    "BUSDUSDT", "WBTCUSDT", "BTCFDUSD", "ETHFDUSD", "BTCUSDC", "ETHUSDC",
    "BNBUSDC", "BTCBUSD", "ETHBUSD", "BNBBUSD", "SOLBUSD", "XRPBUSD",
    "BUSDUSDC", "USDTBUSD", "USDTUSDC", "USTCUSDT", "BETHUSDT", "STETHUSDT",
    "WUSDT", "BFUSD",
}
# leveraged tokens (token names ending in UP/DOWN/BULL/BEAR are excluded by rule)
def _is_leveraged(symbol: str) -> bool:
    base = symbol.removesuffix("USDT")
    return base.endswith(("UP", "DOWN", "BULL", "BEAR"))


@dataclass(frozen=True, slots=True)
class UniverseDefinition:
    """Reproducible universe selection (spec §4)."""
    universe_id: str
    selection_metric: str = "volume_usdt_24h"
    top_n: int = 500
    exclude: tuple[str, ...] = ()
    rebalance: str = "weekly"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    exclude_leveraged: bool = True

    def universe_hash(self) -> str:
        """Deterministic universe id = SHA256(canonical definition)."""
        return dataset_id_of(self.__dict__)

    def accepts(self, symbol: str) -> bool:
        if symbol in self.exclude or symbol in EXCLUDED_SYMBOLS:
            return False
        if self.exclude_leveraged and _is_leveraged(symbol):
            return False
        return symbol.endswith("USDT")


def build_universe(volume_map: dict[str, float], definition: UniverseDefinition) -> dict[str, Tier]:
    """Select top-N symbols by volume and tag tiers (spec §4).

    volume_map: {symbol: volume_usdt_24h}
    Returns: {symbol: tier} — selection metadata, NOT features.
    """
    eligible = {s: v for s, v in volume_map.items() if definition.accepts(s)}
    ranked = sorted(eligible.items(), key=lambda kv: kv[1], reverse=True)
    selected = ranked[: definition.top_n]
    return {symbol: tier_of(vol) for symbol, vol in selected}


def default_universe() -> UniverseDefinition:
    return UniverseDefinition(universe_id="futures_top_liquidity_v1")
