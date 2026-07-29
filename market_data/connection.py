"""Exchange connection — base class for WS connections with reconnect.

Emits ConnectionStatus events on start, stop, and reconnect.
"""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any

from .event_bus import EventBus
from .events import ConnectionStatus, EventType, Exchange, MarketEvent, Timestamps

logger = logging.getLogger(__name__)


class ExchangeConnection(ABC):
    """Base class for exchange WebSocket connections.

    Subclasses define _connect_and_listen, _parse_message, _handle_message.
    """

    def __init__(
        self,
        event_bus: EventBus,
        subscriptions: list[dict[str, Any]],
        exchange: Exchange,
    ) -> None:
        self.event_bus = event_bus
        self.subscriptions = subscriptions
        self.exchange = exchange
        self._is_running = False
        self._connection_task: asyncio.Task | None = None
        self._reconnect_delay = 5

    async def start(self) -> None:
        if not self._is_running:
            self._is_running = True
            self._connection_task = asyncio.create_task(self._run())
            await self.event_bus.publish(
                ConnectionStatus(
                    event_type=EventType.CONNECTION_STATUS,
                    timestamps=Timestamps.now(),
                    exchange=self.exchange,
                    is_connected=True,
                )
            )

    async def stop(self) -> None:
        if self._is_running:
            self._is_running = False
            if self._connection_task:
                self._connection_task.cancel()
                try:
                    await self._connection_task
                except asyncio.CancelledError:
                    logger.info("Connection task for %s cancelled.", self.exchange)
            await self.event_bus.publish(
                ConnectionStatus(
                    event_type=EventType.CONNECTION_STATUS,
                    timestamps=Timestamps.now(),
                    exchange=self.exchange,
                    is_connected=False,
                    reason="stopped",
                ),
            )

    async def _run(self) -> None:
        while self._is_running:
            try:
                await self._connect_and_listen()
            except asyncio.CancelledError:
                logger.info("Connection run loop for %s cancelled.", self.exchange)
                break
            except Exception as e:
                logger.error(
                    "Connection to %s failed: %s. Reconnecting in %.0fs.",
                    self.exchange, e, self._reconnect_delay,
                )
                await self.event_bus.publish(
                    ConnectionStatus(
                        event_type=EventType.CONNECTION_STATUS,
                        timestamps=Timestamps.now(),
                        exchange=self.exchange,
                        is_connected=False,
                        reason=str(e)[:200],
                    ),
                )
                await asyncio.sleep(self._reconnect_delay)
                self._reconnect_delay = min(self._reconnect_delay * 2, 60)
                continue
            await self.event_bus.publish(
                ConnectionStatus(
                    event_type=EventType.CONNECTION_STATUS,
                    timestamps=Timestamps.now(),
                    exchange=self.exchange,
                    is_connected=True,
                ),
            )
        await asyncio.sleep(0)

    @abstractmethod
    async def _connect_and_listen(self) -> None:
        ...

    @abstractmethod
    def _parse_message(self, message: Any) -> MarketEvent | None:
        ...

    @abstractmethod
    async def _handle_message(self, message: Any) -> None:
        ...
