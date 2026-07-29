"""
Implements the data windowing logic as per ADR-004.
"""
from __future__ import annotations
from collections import deque
from dataclasses import dataclass
from typing import Protocol
from market_data.events import Exchange, MarketEvent, EventType
from .models import SymbolFeatureState


@dataclass(slots=True)
class SymbolWindowState:
    """
    Holds the deques for various data windows for a single symbol.
    This is a pure data container.
    """
    trades_1m: deque[MarketEvent]
    candles_1m: deque[MarketEvent]
    oi_1h: deque[MarketEvent]
    funding_8h: deque[MarketEvent]


class WindowManager(Protocol):
    """
    Manages time-based data windows for various market data types
    on a per-symbol basis.
    """

    def append_trade(self, event: MarketEvent) -> None:
        ...

    def append_candle(self, event: MarketEvent) -> None:
        ...

    def append_open_interest(self, event: MarketEvent) -> None:
        ...

    def append_funding(self, event: MarketEvent) -> None:
        ...

    def get_state(self, exchange: Exchange, symbol: str) -> SymbolWindowState:
        ...


class DefaultWindowManager(WindowManager):
    """
    Default implementation of WindowManager.

    Manages data windows for each symbol using a dictionary of SymbolWindowState.
    """
    def __init__(self, max_trades: int = 1000, max_candles: int = 1000, max_oi: int = 1000, max_funding: int = 100):
        self._states: dict[tuple[Exchange, str], SymbolWindowState] = {}
        self.max_trades = max_trades
        self.max_candles = max_candles
        self.max_oi = max_oi
        self.max_funding = max_funding

    def _get_or_create_state(self, exchange: Exchange, symbol: str) -> SymbolWindowState:
        key = (exchange, symbol)
        if key not in self._states:
            self._states[key] = SymbolWindowState(
                trades_1m=deque(maxlen=self.max_trades),
                candles_1m=deque(maxlen=self.max_candles),
                oi_1h=deque(maxlen=self.max_oi),
                funding_8h=deque(maxlen=self.max_funding),
            )
        return self._states[key]

    def append_trade(self, event: MarketEvent) -> None:
        if event.event_type != EventType.TRADE:
            return
        state = self._get_or_create_state(event.exchange, event.symbol)
        state.trades_1m.append(event)

    def append_candle(self, event: MarketEvent) -> None:
        if event.event_type != EventType.CANDLE_1M:
            return
        state = self._get_or_create_state(event.exchange, event.symbol)
        state.candles_1m.append(event)

    def append_open_interest(self, event: MarketEvent) -> None:
        if event.event_type != EventType.OPEN_INTEREST:
            return
        state = self._get_or_create_state(event.exchange, event.symbol)
        state.oi_1h.append(event)

    def append_funding(self, event: MarketEvent) -> None:
        if event.event_type != EventType.FUNDING:
            return
        state = self._get_or_create_state(event.exchange, event.symbol)
        state.funding_8h.append(event)

    def get_state(self, exchange: Exchange, symbol: str) -> SymbolWindowState:
        return self._get_or_create_state(exchange, symbol)
