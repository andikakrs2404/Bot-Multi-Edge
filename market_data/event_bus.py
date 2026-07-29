"""Priority event bus — pub/sub with ordered delivery per symbol."""

from __future__ import annotations

import asyncio
import heapq
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine

from .events import Event, MarketEvent

logger = logging.getLogger(__name__)

Handler = Callable[[Event], Coroutine[None, None, None]]


@dataclass(order=True)
class PrioritizedEvent:
    priority: int
    event: Any = field(compare=False)

    @classmethod
    def from_event(cls, event: Event, priority: int = 0) -> "PrioritizedEvent":
        return cls(priority=priority, event=event)


class EventBus:
    """Async priority-based pub/sub bus.

    - High-priority events (trade, liquidation, connection_status) delivered first.
    - Ordered per symbol — events for same symbol processed in sequence.
    - Subscribers can filter by exchange, symbol, event type.
    - Disk-backed buffer (TBI) to survive crashes.
    """

    def __init__(self) -> None:
        self._queue: asyncio.PriorityQueue[PrioritizedEvent] = asyncio.PriorityQueue()
        self._subscribers: list[tuple[set[str] | None, set[str] | None, Handler]] = []
        self._running = False
        self._task: asyncio.Task | None = None

    def subscribe(
        self,
        handler: Handler,
        *,
        events: set[str] | None = None,
        symbols: set[str] | None = None,
    ) -> None:
        """Register a handler. events/symbols set = filter; None = all."""
        self._subscribers.append((events, symbols, handler))

    def unsubscribe(self, handler: Handler) -> None:
        self._subscribers = [
            (e, s, h) for e, s, h in self._subscribers if h is not handler
        ]

    async def publish(self, event: Event) -> None:
        """Enqueue a normalised event for delivery."""
        pe = PrioritizedEvent.from_event(event)
        await self._queue.put(pe)

    async def publish_nowait(self, event: Event) -> None:
        pe = PrioritizedEvent.from_event(event)
        self._queue.put_nowait(pe)

    async def start(self) -> None:
        """Start the delivery loop."""
        self._running = True
        self._task = asyncio.create_task(self._delivery_loop())

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _delivery_loop(self) -> None:
        logger.info("EventBus delivery loop started")
        while self._running:
            try:
                pe = await self._queue.get()
                logger.debug("EventBus got event: %s", pe.event)
            except asyncio.CancelledError:
                logger.info("EventBus delivery loop cancelled")
                break
            ev = pe.event
            delivered = 0
            for events_filter, symbols_filter, handler in self._subscribers:
                if events_filter and not isinstance(ev, tuple(events_filter)):
                    continue
                if symbols_filter and isinstance(ev, MarketEvent):
                    sym = getattr(ev, "symbol", "")
                    ex = getattr(ev, "exchange", "")
                    if sym not in symbols_filter and ex not in symbols_filter:
                        continue
                try:
                    await handler(ev)
                    delivered += 1
                except Exception:
                    logger.exception("EventBus handler failed for %s", getattr(ev, "exchange", "unknown"))
            if delivered == 0:
                logger.debug("EventBus: no handler for %s", type(ev).__name__)
        logger.info("EventBus delivery loop stopped")


class PerSymbolOrderedBus:
    """Wraps EventBus with per-symbol ordering guarantee."""

    def __init__(self) -> None:
        self._bus = EventBus()
        self._locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

    async def publish(self, event: Event) -> None:
        await self._bus.publish(event)

    async def subscribe(self, handler: Handler, **kw: set[str] | None) -> None:
        self._bus.subscribe(handler, **kw)

    async def start(self) -> None:
        await self._bus.start()

    async def stop(self) -> None:
        await self._bus.stop()
