"""Bybit Futures WS message adapter — parses V5 public linear streams.

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

_TOPICS: dict[str, str] = {
    "ticker": "tickers.{symbol}",
    "trade": "publicTrade.{symbol}",
    "liquidation": "liquidation.{symbol}",
    "orderbook": "orderbook.200.{symbol}",
    "kline_1m": "kline.1.{symbol}",
    "kline_15m": "kline.15.{symbol}",
    "kline_1h": "kline.1.{symbol}",
}


def build_subscribe(symbols: list[str]) -> dict[str, Any]:
    """Build Bybit V5 WS subscribe payload."""
    args = []
    for s in symbols:
        args.append(_TOPICS["ticker"].format(symbol=s))
        args.append(_TOPICS["trade"].format(symbol=s))
        args.append(_TOPICS["liquidation"].format(symbol=s))
    return {"op": "subscribe", "args": args}


def parse_message(raw: bytes | str) -> list[MarketEvent] | None:
    """Parse a raw Bybit WS message into MarketEvent(s). Returns None if no event."""
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", errors="replace")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("Bybit invalid JSON: %s", raw[:200])
        return None

    # heartbeat
    if data.get("op") == "pong" or data.get("type") == "heartbeat":
        return None

    if data.get("success") is False:
        logger.warning("Bybit sub error: %s", data.get("ret_msg"))
        return None

    topic: str | None = data.get("topic")
    if not topic:
        return None

    ts_data = data.get("ts") or data.get("timestamp") or time.time()
    exchange_ts = _parse_ts(ts_data)
    results: list[MarketEvent] = []

    for item in data.get("data", []):
        symbol: str = item.get("symbol", "")
        if not symbol:
            continue

        event_type = _topic_to_event(topic)
        payload = _extract_payload(event_type, item)
        if payload is None:
            continue

        results.append(
            MarketEvent(
                event_type=event_type,
                timestamps=Timestamps.now(exchange_ts=exchange_ts),
                exchange=Exchange.BYBIT,
                symbol=symbol,
                data=payload,
            )
        )

    return results or None


def heartbeat() -> str:
    return json.dumps({"op": "ping"})


# ── internal helpers ──


def _topic_to_event(topic: str) -> EventType:
    if topic.startswith("publicTrade"):
        return EventType.TRADE
    elif topic.startswith("liquidation"):
        return EventType.LIQUIDATION
    elif topic.startswith("tickers"):
        return EventType.TICKER
    elif "kline" in topic:
        if "1m" in topic:
            return EventType.CANDLE_1M
        elif "15m" in topic:
            return EventType.CANDLE_15M
        return EventType.CANDLE_1H
    return EventType.TICKER


def _extract_payload(event_type: EventType, item: dict[str, Any]) -> dict[str, Any] | None:
    if event_type == EventType.TRADE:
        return {
            "price": float(item.get("p", 0)),
            "size": float(item.get("v", 0)),
            "side": item.get("S", "Buy").lower(),
            "trade_id": item.get("i", ""),
            "seq": item.get("seq", 0),
        }
    elif event_type == EventType.LIQUIDATION:
        return {
            "price": float(item.get("p", 0)),
            "size": float(item.get("v", 0)),
            "side": item.get("S", "Buy").lower(),
        }
    elif event_type == EventType.TICKER:
        bid = float(item.get("bid1Price", 0))
        ask = float(item.get("ask1Price", 0))
        return {
            "price": float(item.get("lastPrice", 0)),
            "volume_24h": float(item.get("volume24h", 0)),
            "oi": float(item.get("openInterest", 0)),
            "funding_rate": float(item.get("fundingRate", 0)),
            "mark_price": float(item.get("markPrice", 0)),
            "index_price": float(item.get("indexPrice", 0)),
            "bid": bid,
            "ask": ask,
            "spread": ask - bid,
            "turnover_24h": float(item.get("turnover24h", 0)),
        }
    return None


def _parse_ts(ts: Any) -> datetime | None:
    """Convert ms timestamp to UTC datetime."""
    try:
        return datetime.fromtimestamp(int(ts) / 1000.0, tz=timezone.utc)
    except (ValueError, TypeError):
        return None
