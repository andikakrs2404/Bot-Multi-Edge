"""In-memory ring buffers with TTL for observability data."""

from __future__ import annotations

import asyncio
import time
from collections import deque
from dataclasses import dataclass
from typing import Any

from src.market_data.events import ConnectionStatus


@dataclass
class _StoredEvent:
    timestamp: float
    data: Any


class ObservabilityStore:
    """Thread-safe in-memory store for connection status & recent metrics.

    ConnectionStatus events: ring buffer per exchange key (last N).
    General metrics: single deque with maxlen.
    TTL eviction runs on read.
    """

    def __init__(
        self,
        max_per_exchange: int = 100,
        max_metrics: int = 1000,
        ttl_sec: float = 3600.0,
    ) -> None:
        self._max_per_exchange = max_per_exchange
        self._max_metrics = max_metrics
        self._ttl_sec = ttl_sec
        self._lock = asyncio.Lock()

        self._connections: dict[str, deque[_StoredEvent]] = {}
        self._reconnect_counts: dict[str, int] = {}
        # general metrics ring buffer
        self._metrics: deque[_StoredEvent] = deque(maxlen=max_metrics)

    async def push_connection_status(self, exchange: str, status: Any) -> None:
        async with self._lock:
            if exchange not in self._connections:
                self._connections[exchange] = deque(maxlen=self._max_per_exchange)
            self._connections[exchange].append(_StoredEvent(time.time(), status))
            if getattr(status, "is_connected", True) is False:
                self._reconnect_counts[exchange] = (
                    self._reconnect_counts.get(exchange, 0) + 1
                )

    async def update_from_connection_status(
        self, exchange: str, status: ConnectionStatus
    ) -> None:
        """Update store from a ConnectionStatus event."""
        async with self._lock:
            if exchange not in self._connections:
                self._connections[exchange] = deque(maxlen=self._max_per_exchange)
            self._connections[exchange].append(
                _StoredEvent(time.time(), status)
            )
            if not status.is_connected:
                self._reconnect_counts[exchange] = (
                    self._reconnect_counts.get(exchange, 0) + 1
                )

    async def push_metric(self, metric: Any) -> None:
        async with self._lock:
            self._metrics.append(_StoredEvent(time.time(), metric))

    async def get_connection_status(self, exchange: str) -> list[Any]:
        async with self._lock:
            return self._evict(self._connections.get(exchange))

    async def get_all_connections(self) -> dict[str, list[Any]]:
        async with self._lock:
            result: dict[str, list[Any]] = {}
            for key, deq in self._connections.items():
                events = self._evict(deq)
                if events:
                    result[key] = events
            return result

    async def latest_status(self, exchange: str) -> Any | None:
        events = await self.get_connection_status(exchange)
        return events[-1] if events else None

    async def reconnect_count(self, exchange: str) -> int:
        async with self._lock:
            return self._reconnect_counts.get(exchange, 0)

    async def get_recent_metrics(self, limit: int = 50) -> list[Any]:
        async with self._lock:
            cutoff = time.time() - self._ttl_sec
            valid = [s.data for s in self._metrics if s.timestamp >= cutoff]
            return valid[-limit:]

    def _evict(self, deq: deque[_StoredEvent] | None) -> list[Any]:
        if not deq:
            return []
        cutoff = time.time() - self._ttl_sec
        while deq and deq[0].timestamp < cutoff:
            deq.popleft()
        return [s.data for s in deq]
