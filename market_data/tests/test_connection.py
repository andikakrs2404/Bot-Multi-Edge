import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock

from src.market_data.connection import ExchangeConnection
from src.market_data.event_bus import EventBus
from src.market_data.events import ConnectionStatus, Exchange, MarketEvent


class MockExchangeConnection(ExchangeConnection):
    def __init__(self, event_bus: EventBus, subscriptions):
        super().__init__(event_bus, subscriptions, Exchange.BINANCE)
        self.parse_message_mock = MagicMock()
        self.handle_message_mock = MagicMock()

    async def _connect_and_listen(self):
        await asyncio.Event().wait()

    def _parse_message(self, message: str) -> MarketEvent | None:
        return self.parse_message_mock(message)

    async def _handle_message(self, message: str):
        self.handle_message_mock(message)


class TestExchangeConnection(unittest.TestCase):
    def setUp(self):
        self.event_bus = EventBus()
        self.subscriptions = [{"type": "trade", "symbol": "BTC/USDT"}]

    def test_connection_start_stop(self):
        async def run_test():
            await self.event_bus.start()
            conn = MockExchangeConnection(self.event_bus, self.subscriptions)
            self.assertFalse(conn._is_running)
            self.assertIsNone(conn._connection_task)

            await conn.start()
            self.assertTrue(conn._is_running)
            self.assertIsNotNone(conn._connection_task)

            await conn.stop()
            self.assertFalse(conn._is_running)
            await asyncio.sleep(0.02)
            self.assertTrue(conn._connection_task.done())

        asyncio.run(run_test())

    def test_connection_reconnect_on_failure(self):
        async def run_test():
            await self.event_bus.start()
            conn = MockExchangeConnection(self.event_bus, self.subscriptions)
            conn._connect_and_listen = AsyncMock(
                side_effect=[asyncio.TimeoutError, asyncio.Event().wait]
            )
            conn._reconnect_delay = 0.1

            status_events = []

            async def collector(ev):
                if isinstance(ev, ConnectionStatus):
                    status_events.append(ev)

            self.event_bus.subscribe(collector)

            await conn.start()
            await asyncio.sleep(0.25)
            await conn.stop()

            self.assertGreaterEqual(len(status_events), 3)
            self.assertTrue(status_events[0].is_connected)
            self.assertFalse(status_events[1].is_connected)
            self.assertTrue(status_events[2].is_connected)
            self.assertGreaterEqual(conn._connect_and_listen.call_count, 2)

        asyncio.run(run_test())


if __name__ == "__main__":
    unittest.main()
