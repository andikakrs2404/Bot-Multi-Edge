"""Event schemas — Phase 1 contract (frozen).

Hierarchy:
  Event (base, all events)
   ├── MarketEvent     (market data: ticker, trade, candle, ...)
   ├── ConnectionStatus (exchange connectivity)
   └── SymbolEvent     (registry: added/removed)

No PRIORITY_MAP here — priority lives at Opportunity Pipeline layer (ADR-011).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class Exchange(str, Enum):
    BYBIT = "BYBIT"
    BINANCE = "BINANCE"

    def __str__(self) -> str:
        return self.value


class EventType(str, Enum):
    # Market data (ADR-002)
    TICKER = "ticker"
    TRADE = "trade"
    CANDLE_1M = "candle_1m"
    CANDLE_15M = "candle_15m"
    CANDLE_1H = "candle_1h"
    OPEN_INTEREST = "open_interest"
    FUNDING = "funding"
    LIQUIDATION = "liquidation"
    BOOK_SNAPSHOT = "book_snapshot"

    # Connection (ADR-002)
    CONNECTION_STATUS = "connection_status"

    # Registry (ADR-002)
    SYMBOL_ADDED = "symbol_added"
    SYMBOL_REMOVED = "symbol_removed"

    # Placeholder — Feature Store / Screener events added in later phases


@dataclass(slots=True)
class Timestamps:
    """Triple-timestamp envelope per ADR-002 and ADR-004."""
    exchange_ts: datetime | None
    received_ts: datetime
    processed_ts: datetime | None = None

    @classmethod
    def now(cls, exchange_ts: datetime | None = None) -> Timestamps:
        now = datetime.now(timezone.utc)
        return cls(exchange_ts=exchange_ts or now, received_ts=now)


@dataclass(slots=True)
class Event:
    """Base event — every system event carries these."""
    event_type: EventType
    timestamps: Timestamps
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])


@dataclass(slots=True, kw_only=True)
class MarketEvent(Event):
    """Market data payload — ticker, trade, liquidation, candle, book, ..."""
    exchange: Exchange
    symbol: str
    data: dict[str, Any]


@dataclass(slots=True, kw_only=True)
class ConnectionStatus(Event):
    """Exchange connection state change."""
    exchange: Exchange
    is_connected: bool
    reason: str | None = None


@dataclass(slots=True, kw_only=True)
class SymbolEvent(Event):
    """Registry lifecycle event — symbol added or removed."""
    exchange: Exchange
    symbol: str
    metadata: dict[str, Any]
