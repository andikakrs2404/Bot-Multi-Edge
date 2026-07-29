"""
FeatureStore — authoritative state owner per ADR-004.

Ingest → route → handler → state update → version bump → FeatureUpdateEvent (lightweight).
Downstream pulls from store, not from bus.
"""
from __future__ import annotations

import asyncio
import time
import logging
from collections import deque, Counter
from typing import Protocol

from market_data.events import MarketEvent, EventType, Exchange
from market_data.event_bus import EventBus
from .models import RawFeature, SymbolFeatureState, FeatureUpdateEvent
from .windows import WindowManager, DefaultWindowManager
from .registry import FeatureId

logger = logging.getLogger(__name__)

# ── routing table ──

class FeatureHandler(Protocol):
    handler_id: str
    def handle(self, event: MarketEvent, windows: object, state: SymbolFeatureState) -> list[RawFeature]: ...


_EVENT_HANDLER_MAP: dict[EventType, str] = {
    EventType.TICKER: "ticker",
    EventType.TRADE: "trade",
    EventType.CANDLE_1M: "candle",
    EventType.OPEN_INTEREST: "open_interest",
    EventType.FUNDING: "funding",
    EventType.LIQUIDATION: "liquidation",
}


class FeatureStore:
    """Authoritative state owner. Ingest, route, compute, store, notify."""

    def __init__(
        self,
        bus: EventBus | None,
        handlers: dict[str, FeatureHandler] | None = None,
        windows: WindowManager | None = None,
    ) -> None:
        if handlers is None:
            handlers = {}
        if bus is None:
            # dummy bus for testing
            class DummyBus:
                def subscribe(self, *args, **kwargs): pass
                async def publish(self, *args, **kwargs): pass
            bus = DummyBus()

        self._bus = bus
        self._handlers = handlers
        self._windows = windows or DefaultWindowManager()

        # State: Exchange → symbol → SymbolFeatureState
        self._states: dict[Exchange, dict[str, SymbolFeatureState]] = {}
        self._versions: dict[tuple[Exchange, str], int] = {}
        self._feature_versions: dict[tuple[Exchange, str, FeatureId], int] = {}

        # Pre-build router: EventType → FeatureHandler
        self._router: dict[EventType, FeatureHandler] = {}
        for et, h_id in _EVENT_HANDLER_MAP.items():
            if h_id in handlers:
                self._router[et] = handlers[h_id]

        # ── observability ──
        self.metrics: dict[str, int] = {
            "events_ingested": 0,
            "feature_updates": 0,
            "active_symbols": 0,
            "handler_errors": 0,
        }
        self._handler_counts: Counter[str] = Counter()
        self._update_timestamps: deque[float] = deque(maxlen=10_000)

        # ── freshness ──
        self._freshness_task: asyncio.Task | None = None
        self._freshness_interval: float = 30.0
        self._stale_features: list[dict] = []

    # ── lifecycle ──

    async def start(self) -> None:
        self._bus.subscribe(self._on_event)
        logger.info("FeatureStore subscribed (%d event types)", len(self._router))

    async def stop(self) -> None:
        await self.stop_freshness_checks()

    # ── freshness loop ──

    async def start_freshness_checks(self, interval_sec: float = 30.0) -> None:
        self._freshness_interval = interval_sec
        if self._freshness_task is None or self._freshness_task.done():
            self._freshness_task = asyncio.create_task(self._freshness_loop())

    async def stop_freshness_checks(self) -> None:
        if self._freshness_task and not self._freshness_task.done():
            self._freshness_task.cancel()
            try:
                await self._freshness_task
            except asyncio.CancelledError:
                pass
            self._freshness_task = None

    async def _freshness_loop(self) -> None:
        while True:
            await asyncio.sleep(self._freshness_interval)
            self._check_freshness()

    def _check_freshness(self) -> None:
        now = time.monotonic()
        stale: list[dict] = []
        for exch, sym_map in self._states.items():
            for sym, state in sym_map.items():
                for fid, rf in state.features.items():
                    age = now - rf.computed_at
                    if age > rf.ttl:
                        stale.append({
                            "exchange": exch.value,
                            "symbol": sym,
                            "feature": fid.value,
                            "status": "STALE",
                            "age": round(age, 1),
                        })
        self._stale_features = stale
        if stale:
            logger.debug("freshness: %d stale features", len(stale))

    # ── public query ──

    def get_feature(
        self,
        exchange: Exchange,
        symbol: str,
        feature: FeatureId,
        now: float | None = None,
    ) -> RawFeature | None:
        """Return fresh RawFeature or None if stale / missing."""
        state = self._states.get(exchange, {}).get(symbol)
        if state is None:
            return None
        rf = state.features.get(feature)
        if rf is None:
            return None
        age = (now or time.monotonic()) - rf.computed_at
        if age > rf.ttl:
            return None
        return rf

    def get_symbol_state(
        self,
        exchange: Exchange,
        symbol: str,
    ) -> SymbolFeatureState | None:
        return self._states.get(exchange, {}).get(symbol)

    def get_window_state(self, exchange: Exchange, symbol: str) -> object:
        return self._windows.get_state(exchange, symbol)

    # legacy alias
    def get_state(self, exchange: str, symbol: str) -> SymbolFeatureState | None:
        """Deprecated: use get_symbol_state(). Accepts str exchange for backward compat."""
        try:
            ex = Exchange(exchange)
        except ValueError:
            return None
        return self.get_symbol_state(ex, symbol)

    def stats(self) -> dict:
        """Snapshot of store health."""
        sym_count = 0
        feat_count = 0
        feat_coverage: Counter[FeatureId] = Counter()
        for sym_map in self._states.values():
            sym_count += len(sym_map)
            for state in sym_map.values():
                feat_count += len(state.features)
                for fid in state.features:
                    feat_coverage[fid] += 1

        # updates/sec over last 60s from rolling timestamp window
        now = time.monotonic()
        cutoff = now - 60.0
        recent = sum(1 for t in self._update_timestamps if t >= cutoff)
        ups = round(recent / 60.0, 1) if recent > 0 else 0.0

        total_feats_sym = sym_count * len(FeatureId) if sym_count else 1
        coverage_pct = round(feat_count / total_feats_sym * 100, 1) if feat_count else 0.0

        return {
            "symbols": sym_count,
            "features": feat_count,
            "updates": self.metrics["feature_updates"],
            "updates_per_sec": ups,
            "handlers": len(self._handlers),
            "handler_counts": dict(self._handler_counts),
            "stale_count": len(self._stale_features),
            "fresh_count": feat_count - len(self._stale_features),
            "coverage_pct": coverage_pct,
            "feature_coverage": {k.value: v for k, v in feat_coverage.most_common()},
        }

    # ── core ingest ──

    async def _on_event(self, event: object) -> None:
        if not isinstance(event, MarketEvent):
            return
        handler = self._router.get(event.event_type)
        if handler is None:
            return

        self.metrics["events_ingested"] += 1
        self._handler_counts[handler.handler_id] += 1
        key = (event.exchange, event.symbol)

        sym_map = self._states.setdefault(event.exchange, {})
        state = sym_map.get(event.symbol)
        if state is None:
            state = SymbolFeatureState(exchange=event.exchange.value, symbol=event.symbol)
            sym_map[event.symbol] = state
            self.metrics["active_symbols"] += 1

        windows = self._windows.get_state(event.exchange, event.symbol)

        # 1. update windows
        self._append_to_windows(event)
        windows = self._windows.get_state(event.exchange, event.symbol)

        # 2. compute
        try:
            raw_features = handler.handle(event, windows, state)
        except Exception:
            self.metrics["handler_errors"] += 1
            raise

        # 3. update state + versions
        if not raw_features:
            return
        self.metrics["feature_updates"] += 1
        self._update_timestamps.append(time.monotonic())

        version = self._versions.get(key, 0) + 1
        self._versions[key] = version

        changed: list[FeatureId] = []
        now = time.monotonic()
        for rf in raw_features:
            state.update(rf)
            # per-feature version bump for downstream change-detection
            self._feature_versions[(event.exchange, event.symbol, rf.feature)] = \
                self._feature_versions.get((event.exchange, event.symbol, rf.feature), 0) + 1
            changed.append(rf.feature)

        # 4. publish lightweight notification
        notification = FeatureUpdateEvent(
            exchange=event.exchange.value,
            symbol=event.symbol,
            changed=changed,
            version=version,
            computed_at=now,
        )
        await self._bus.publish(notification)

    def _append_to_windows(self, event: MarketEvent) -> None:
        et = event.event_type
        if et == EventType.TRADE:
            self._windows.append_trade(event)
        elif et == EventType.CANDLE_1M:
            self._windows.append_candle(event)
        elif et == EventType.OPEN_INTEREST:
            self._windows.append_open_interest(event)
        elif et == EventType.FUNDING:
            self._windows.append_funding(event)
        # TICKER / LIQUIDATION not windowed
