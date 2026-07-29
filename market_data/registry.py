"""Symbol Registry — auto-discover, track lifecycle, serve metadata.

Polls exchange REST APIs, emits SymbolEvent for additions / removals.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any

import httpx

from .event_bus import EventBus
from .events import EventType, Exchange, SymbolEvent, Timestamps

logger = logging.getLogger(__name__)


@dataclass
class SymbolMeta:
    symbol: str
    exchange: Exchange | str
    sector: str = "UNKNOWN"
    tags: list[str] = field(default_factory=list)
    listing_age_days: int = 0
    market_cap_tier: str = "unknown"
    status: str = "ACTIVE"
    first_seen: float = 0.0
    last_seen: float = 0.0


SymbolMetaDict = dict[str, SymbolMeta]


class SymbolRegistry:
    """Auto-discovers symbols from exchange REST APIs.

    - Polls every interval_sec
    - Detects new listings, delistings
    - Publishes SymbolEvent on event_bus
    """

    def __init__(
        self,
        event_bus: EventBus,
        interval_sec: float = 300.0,
        delist_consecutive_misses: int = 2,
    ) -> None:
        self._event_bus = event_bus
        self._interval = interval_sec
        self._delist_threshold = delist_consecutive_misses
        self._symbols: SymbolMetaDict = {}
        self._miss_count: dict[str, int] = {}

    async def start(self) -> None:
        logger.info("SymbolRegistry started (poll every %.0fs)", self._interval)
        await self._poll()
        while True:
            await asyncio.sleep(self._interval)
            await self._poll()

    async def _poll(self) -> None:
        for exchange, api_url, api_params in [
            (Exchange.BYBIT, "https://api.bybit.com/v5/market/instruments-info", {"category": "linear"}),
            (Exchange.BINANCE, "https://fapi.binance.com/fapi/v1/exchangeInfo", None),
        ]:
            try:
                async with httpx.AsyncClient(timeout=15) as client:
                    r = await client.get(api_url, params=api_params)
                    r.raise_for_status()
                    data = r.json()
                symbols = self._parse_response(exchange, data)
                await self._update(exchange, symbols)
            except Exception as exc:
                logger.warning("SymbolRegistry poll %s failed: %s", exchange, exc)

    def _parse_response(self, exchange: Exchange, data: dict) -> dict[str, SymbolMeta]:
        result: dict[str, SymbolMeta] = {}
        if exchange == Exchange.BYBIT:
            for item in data.get("result", {}).get("list", []):
                if item.get("status") != "Trading":
                    continue
                symbol = item["symbol"]
                result[symbol] = SymbolMeta(
                    symbol=symbol,
                    exchange=exchange,
                    sector=_infer_sector(symbol),
                    listing_age_days=0,
                )
        elif exchange == Exchange.BINANCE:
            for item in data.get("symbols", []):
                if item.get("status") != "TRADING":
                    continue
                if item.get("contractType") != "PERPETUAL":
                    continue
                symbol = item["pair"]
                result[symbol] = SymbolMeta(
                    symbol=symbol,
                    exchange=exchange,
                    sector=_infer_sector(symbol),
                    listing_age_days=0,
                )
        return result

    async def _update(self, exchange: Exchange, incoming: dict[str, SymbolMeta]) -> None:
        now = time.time()
        seen_this_poll: set[str] = set()

        for key, meta in incoming.items():
            full_key = f"{exchange}:{key}"
            seen_this_poll.add(full_key)
            self._miss_count[full_key] = 0

            if full_key not in self._symbols:
                meta.first_seen = now
                meta.last_seen = now
                self._symbols[full_key] = meta
                logger.info("New symbol: %s", full_key)
                await self._publish_symbol_event(
                    EventType.SYMBOL_ADDED, exchange, key,
                    {"sector": meta.sector, "tags": meta.tags},
                )
            else:
                existing = self._symbols[full_key]
                existing.last_seen = now
                if existing.listing_age_days == 0 and existing.first_seen > 0:
                    existing.listing_age_days = int((now - existing.first_seen) / 86400)

        # delist detection
        for full_key in list(self._symbols.keys()):
            if full_key.startswith(f"{exchange}:"):
                if full_key not in seen_this_poll:
                    self._miss_count[full_key] += 1
                    if self._miss_count[full_key] >= self._delist_threshold:
                        meta = self._symbols.pop(full_key, None)
                        if meta:
                            meta.status = "DELISTED"
                            _, sym = full_key.split(":", 1)
                            logger.info("Delisted: %s", full_key)
                            await self._publish_symbol_event(
                                EventType.SYMBOL_REMOVED, exchange, sym,
                                {"reason": "delisted"},
                            )

    async def _publish_symbol_event(
        self,
        event_type: EventType,
        exchange: Exchange,
        symbol: str,
        metadata: dict[str, Any],
    ) -> None:
        await self._event_bus.publish(
            SymbolEvent(
                event_type=event_type,
                timestamps=Timestamps.now(),
                exchange=exchange,
                symbol=symbol,
                metadata=metadata,
            )
        )

    def get(self, exchange: Exchange | str, symbol: str) -> SymbolMeta | None:
        return self._symbols.get(f"{exchange}:{symbol}")

    def list_active(self, exchange: Exchange | None = None) -> list[SymbolMeta]:
        if exchange:
            return [
                m for k, m in self._symbols.items()
                if k.startswith(f"{exchange}:") and m.status == "ACTIVE"
            ]
        return [m for m in self._symbols.values() if m.status == "ACTIVE"]

    @property
    def count(self) -> int:
        return len(self._symbols)

# ── sector inference (heuristic — SPEC-Sector-Classification replaces later) ──


_SECTOR_KEYWORDS: dict[str, list[str]] = {
    "AI": ["AI", "FET", "AGIX", "OCEAN", "RNDR", "TAO", "ARKM", "WLD", "GRT"],
    "DEFI": ["UNI", "AAVE", "CRV", "MKR", "COMP", "SUSHI", "CAKE", "LQTY", "SNX"],
    "MEME": ["DOGE", "SHIB", "PEPE", "WIF", "BONK", "FLOKI", "ORDI", "SATS"],
    "LAYER1": ["BTC", "ETH", "SOL", "AVAX", "NEAR", "FTM", "ADA", "DOT"],
    "LAYER2": ["ARB", "OP", "MATIC", "STARK", "ZKSYNC"],
    "DEX": ["UNI", "SUSHI", "CAKE", "1INCH", "DODO"],
    "GAMING": ["GALA", "AXS", "SAND", "MANA", "ENJ", "IMX"],
    "INFRA": ["LINK", "GRT", "AR", "FIL", "LIT", "API3"],
    "RWA": ["ONDO", "POLYX", "CFG", "RIO", "MPL"],
    "DEPIN": ["HNT", "IOTX", "FIL", "AR", "RNDR"],
}


def _infer_sector(symbol: str) -> str:
    """Strip quote suffix + numeric prefix, then match keywords."""
    base = (
        symbol.replace("USDT", "")
        .replace("USDC", "")
        .replace("USD", "")
        .replace("PERP", "")
        .replace("BUSD", "")
    )
    candidates = [base]
    if base and base[0].isdigit():
        stripped = base.lstrip("0123456789")
        if stripped:
            candidates.append(stripped)
    for sector, keywords in _SECTOR_KEYWORDS.items():
        for kw in keywords:
            for c in candidates:
                if c.startswith(kw) or c.endswith(kw):
                    return sector
    return "OTHER"
