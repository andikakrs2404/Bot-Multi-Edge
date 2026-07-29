"""Tests for Market Data Layer — no exchange connection needed."""

from __future__ import annotations

import asyncio
import time

import pytest

from src.market_data.event_bus import EventBus, PrioritizedEvent
from src.market_data.events import (
    ConnectionStatus,
    Event,
    EventType,
    Exchange,
    MarketEvent,
    SymbolEvent,
    Timestamps,
)
from src.market_data.validator import SequenceValidator
from src.market_data.timestamps import enrich_timestamps


class TestPrioritizedEvent:
    def test_ordering(self) -> None:
        low = PrioritizedEvent(priority=10, event="low_p")
        high = PrioritizedEvent(priority=1, event="high_p")
        assert high < low


class TestEventBus:
    @pytest.mark.asyncio
    async def test_publish_deliver(self) -> None:
        bus = EventBus()
        received: list[Event] = []

        async def handler(ev: Event) -> None:
            received.append(ev)

        bus.subscribe(handler)
        await bus.start()

        ev = MarketEvent(
            event_type=EventType.TICKER,
            timestamps=Timestamps.now(),
            exchange=Exchange.BYBIT,
            symbol="BTCUSDT",
            data={"price": 60000.0},
        )
        await bus.publish(ev)
        await asyncio.sleep(0)
        await bus.stop()

        assert len(received) == 1
        assert isinstance(received[0], MarketEvent)
        assert received[0].symbol == "BTCUSDT"

    @pytest.mark.asyncio
    async def test_filter_by_event_type(self) -> None:
        bus = EventBus()
        trades: list[Event] = []

        async def handler(ev: Event) -> None:
            trades.append(ev)

        bus.subscribe(handler, events={MarketEvent})
        await bus.start()

        trade_event = MarketEvent(
            event_type=EventType.TRADE,
            timestamps=Timestamps.now(),
            exchange=Exchange.BINANCE,
            symbol="ETHUSDT",
            data={"price": 3000.0},
        )
        other_event = ConnectionStatus(
            event_type=EventType.CONNECTION_STATUS,
            timestamps=Timestamps.now(),
            exchange=Exchange.BYBIT,
            is_connected=True,
        )

        await bus.publish(other_event)
        await bus.publish(trade_event)
        await asyncio.sleep(0)
        await bus.stop()

        assert len(trades) == 1
        assert isinstance(trades[0], MarketEvent)


class TestSequenceValidator:
    def test_normal_sequence(self) -> None:
        v = SequenceValidator()
        assert v.validate(Exchange.BYBIT, "BTCUSDT", 1) is None
        assert v.validate(Exchange.BYBIT, "BTCUSDT", 2) is None

    def test_duplicate(self) -> None:
        v = SequenceValidator()
        v.validate(Exchange.BYBIT, "BTCUSDT", 42)
        assert v.validate(Exchange.BYBIT, "BTCUSDT", 42) == "duplicate"

    def test_gap(self) -> None:
        v = SequenceValidator()
        v.validate(Exchange.BYBIT, "BTCUSDT", 100)
        assert v.validate(Exchange.BYBIT, "BTCUSDT", 200) == "gap"
        assert v.total_gaps == 1

    def test_out_of_order_buffered(self) -> None:
        v = SequenceValidator()
        v.validate(Exchange.BYBIT, "BTCUSDT", 100)
        v.validate(Exchange.BYBIT, "BTCUSDT", 102)
        assert v.validate(Exchange.BYBIT, "BTCUSDT", 101) == "out_of_order_buffered"


class TestTimestamps:
    def test_enrich(self) -> None:
        ev = ConnectionStatus(
            event_type=EventType.CONNECTION_STATUS,
            timestamps=Timestamps.now(),
            exchange=Exchange.BYBIT,
            is_connected=True,
        )
        enrich_timestamps(ev, exchange_ts=time.time())
        assert ev.timestamps.exchange_ts is not None
        assert ev.timestamps.received_ts is not None
        assert ev.timestamps.processed_ts is not None

    def test_timestamps_now(self) -> None:
        ts = Timestamps.now()
        assert ts.exchange_ts is not None
        assert ts.received_ts is not None
        assert ts.processed_ts is None
