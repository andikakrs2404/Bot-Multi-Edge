"""Binance Futures WS message adapter — parses USDⓈ-M streams.

Produces MarketEvent with EventType and Timestamps.
Standalone parser, not tied to transport.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from typing import Any

from ..events import EventType, Exchange, MarketEvent, Timestamps

logger = logging.getLogger(__name__)

_STREAM_TOPICS: dict[str, str] = {
    "ticker": "{symbol}@ticker",
    "trade": "{symbol}@trade",
    "liquidation": "{symbol}@forceOrder",
    "kline_1m": "{symbol}@kline_1m",
    "kline_15m": "{symbol}@kline_15m",
    "kline_1h": "{symbol}@kline_1h",
}


def build_subscribe(symbols: list[str]) -> dict[str, Any]:
    """Build Binance WS subscribe payload."""
    params = []
    for s in symbols:
        params.append(_STREAM_TOPICS["ticker"].format(symbol=s.lower()))
        params.append(_STREAM_TOPICS["trade"].format(symbol=s.lower()))
    return {
        "method": "SUBSCRIBE",
        "params": params,
        "id": int(time.time() * 1000) % 100000,
    }


def parse_message(raw: bytes | str) -> list[MarketEvent] | None:
    """Parse raw Binance WS message into MarketEvent(s). Returns None if no event."""
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", errors="replace")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None

    # heartbeat / sub ack — no event field
    if data.get("e") is None:
        return None

    event_type_str = data["e"]
    symbol = data.get("s", "").upper()
    if not symbol:
        return None

    exchange_ts = _parse_ts(data.get("E"))
    event_type = _str_to_type(event_type_str)
    if event_type is None:
        return None

    payload = _extract_payload(event_type, data)
    if payload is None:
        return None

    return [
        MarketEvent(
            event_type=event_type,
            timestamps=Timestamps.now(exchange_ts=exchange_ts),
            exchange=Exchange.BINANCE,
            symbol=symbol,
            data=payload,
        )
    ]


def heartbeat() -> None:
    """Binance closes idle WS after 3 min — ping_interval handles it at transport layer."""
    return None


# ── internal helpers ──


def _str_to_type(s: str) -> EventType | None:
    if s == "24hrTicker":
        return EventType.TICKER
    elif s == "trade":
        return EventType.TRADE
    elif s == "forceOrder":
        return EventType.LIQUIDATION
    return None


def _extract_payload(event_type: EventType, data: dict[str, Any]) -> dict[str, Any] | None:
    if event_type == EventType.TICKER:
        bid = float(data.get("b", 0))
        ask = float(data.get("a", 0))
        return {
            "price": float(data.get("c", 0)),
            "volume_24h": float(data.get("v", 0)),
            "oi": float(data.get("q", 0)),  # quote volume ≈ OI proxy
            "funding_rate": float(data.get("F", 0)),
            "mark_price": float(data.get("m", 0)),
            "index_price": float(data.get("i", 0)),
            "bid": bid,
            "ask": ask,
            "spread": ask - bid,
            "turnover_24h": float(data.get("q", 0)),
        }
    elif event_type == EventType.TRADE:
        return {
            "price": float(data.get("p", 0)),
            "size": float(data.get("q", 0)),
            "side": "buy" if data.get("m") is False else "sell",
            "trade_id": str(data.get("t", "")),
        }
    elif event_type == EventType.LIQUIDATION:
        order = data.get("o", {})
        return {
            "price": float(order.get("p", 0)),
            "size": float(order.get("q", 0)),
            "side": order.get("S", "SELL").lower(),
        }
    return None


def _parse_ts(ts: Any) -> datetime | None:
    """Convert ms epoch to UTC datetime."""
    try:
        return datetime.fromtimestamp(int(ts) / 1000.0, tz=timezone.utc)
    except (ValueError, TypeError):
        return None
