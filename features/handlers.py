"""
Feature handlers — one per event type, one handler_id per handler.

Each handler reads MarketEvent + windows + state, returns RawFeature list.
"""
from __future__ import annotations

import time
import statistics
from typing import Protocol

from market_data.events import MarketEvent
from .models import RawFeature, SymbolFeatureState
from .windows import SymbolWindowState
from .registry import FeatureId, FEATURE_REGISTRY


# ── helpers ──

def _feature(id: FeatureId, value: float) -> RawFeature:
    now = time.monotonic()
    defn = FEATURE_REGISTRY[id]
    return RawFeature(feature=id, value=value, version=defn.version, computed_at=now, ttl=defn.ttl)


def _rsi(closes: list[float], period: int = 14) -> float:
    """Simple moving-average RSI. Returns 50.0 when insufficient data."""
    if len(closes) < period + 1:
        return 50.0
    gains: list[float] = []
    losses: list[float] = []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i - 1]
        gains.append(max(diff, 0.0))
        losses.append(max(-diff, 0.0))
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0.0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


# ── protocol ──

class FeatureHandler(Protocol):
    """Process a market event + current windows/state into raw features."""

    handler_id: str

    def handle(
        self,
        event: MarketEvent,
        windows: SymbolWindowState,
        state: SymbolFeatureState,
    ) -> list[RawFeature]:
        ...


# ── T4.1: Ticker ──

class TickerHandler:
    """Extract price, volume_1m, bid_ask_spread, volume_delta from TICKER.

    Expected event.data keys: price (or last), volume (or base_volume),
    bid, ask, buy_volume, sell_volume.
    """

    handler_id: str = "ticker"

    def handle(
        self,
        event: MarketEvent,
        windows: SymbolWindowState,
        state: SymbolFeatureState,
    ) -> list[RawFeature]:
        d = event.data
        features: list[RawFeature] = []

        price_raw = d.get("price") or d.get("last")
        if price_raw is not None:
            features.append(_feature(FeatureId.PRICE, float(price_raw)))

        vol_raw = d.get("volume") or d.get("base_volume")
        if vol_raw is not None:
            features.append(_feature(FeatureId.VOLUME_1M, float(vol_raw)))

        bid_raw = d.get("bid")
        ask_raw = d.get("ask")
        if bid_raw is not None and ask_raw is not None:
            bid = float(bid_raw)
            ask = float(ask_raw)
            if bid > 0 and ask > 0:
                spread = (ask - bid) / ((ask + bid) / 2.0) * 100.0
                features.append(_feature(FeatureId.BID_ASK_SPREAD, spread))

        buy_raw = d.get("buy_volume")
        sell_raw = d.get("sell_volume")
        if buy_raw is not None and sell_raw is not None:
            delta = float(buy_raw) - float(sell_raw)
            features.append(_feature(FeatureId.VOLUME_DELTA, delta))

        return features


# ── T4.2: Trade ──

class TradeHandler:
    """Extract vwap_1m, trade_count_1m from TRADE + trades_1m window.

    Expected event.data keys: price, volume.
    """

    handler_id: str = "trade"

    def handle(
        self,
        event: MarketEvent,
        windows: SymbolWindowState,
        state: SymbolFeatureState,
    ) -> list[RawFeature]:
        features: list[RawFeature] = []
        trades = windows.trades_1m

        # trade_count_1m: number of trades in window (includes current)
        features.append(_feature(FeatureId.TRADE_COUNT_1M, float(len(trades))))

        # vwap_1m: volume-weighted average price over window
        total_vol = 0.0
        total_notional = 0.0
        for t in trades:
            vol = float(t.data.get("volume", 0) or 0)
            price = float(t.data.get("price", 0) or 0)
            total_vol += vol
            total_notional += vol * price

        vwap = total_notional / total_vol if total_vol > 0 else float(event.data.get("price", 0) or 0)
        features.append(_feature(FeatureId.VWAP_1M, vwap))

        return features


# ── T4.3: Open Interest ──

class OpenInterestHandler:
    """Extract oi, oi_change_1m from OPEN_INTEREST event.

    Expected event.data key: open_interest.
    oi_change_1m requires previous OI in state (computed as tick-to-tick % change).
    """

    handler_id: str = "open_interest"

    def handle(
        self,
        event: MarketEvent,
        windows: SymbolWindowState,
        state: SymbolFeatureState,
    ) -> list[RawFeature]:
        d = event.data
        features: list[RawFeature] = []

        oi = float(d.get("open_interest", 0))
        features.append(_feature(FeatureId.OI, oi))

        # oi_change_1m: % change from last known OI in state
        now = time.monotonic()
        prev = state.get(FeatureId.OI, now)
        if prev is not None and prev != 0:
            change = (oi - prev) / abs(prev) * 100.0
            features.append(_feature(FeatureId.OI_CHANGE_1M, change))
        else:
            features.append(_feature(FeatureId.OI_CHANGE_1M, 0.0))

        # oi_1h_change: % change from oldest retained OI in 1h window.
        # ponytail: no timestamp pruning yet; WindowManager currently bounds by maxlen only.
        oldest = windows.oi_1h[0] if windows.oi_1h else None
        if oldest is not None:
            base = float(oldest.data.get("open_interest", 0) or 0)
            oi_1h_change = (oi - base) / abs(base) * 100.0 if base != 0 else 0.0
        else:
            oi_1h_change = 0.0
        features.append(_feature(FeatureId.OI_1H_CHANGE, oi_1h_change))

        return features


# ── T6A: Funding ──

class FundingHandler:
    """Extract funding_rate, funding_zscore from FUNDING + funding_8h window.

    Expected event.data key: funding_rate.
    zscore uses last 24 funding snapshots from window.
    """

    handler_id: str = "funding"

    def handle(
        self,
        event: MarketEvent,
        windows: SymbolWindowState,
        state: SymbolFeatureState,
    ) -> list[RawFeature]:
        features: list[RawFeature] = []

        rate_raw = event.data.get("funding_rate")
        if rate_raw is None:
            return features
        rate = float(rate_raw)
        features.append(_feature(FeatureId.FUNDING_RATE, rate))

        # zscore vs last 24 funding values
        values = [float(e.data.get("funding_rate", 0) or 0) for e in windows.funding_8h]
        values = [v for v in values if v != 0]

        if len(values) >= 2:
            mu = statistics.mean(values)
            sd = statistics.stdev(values) if len(values) > 1 else 0.0
            z = (rate - mu) / sd if sd > 0 else 0.0
        else:
            z = 0.0

        features.append(_feature(FeatureId.FUNDING_ZSCORE, z))

        return features


# ── T6B: Candle ──

class CandleHandler:
    """Extract high_1m, low_1m, volatility_1m, rsi_14_1m from CANDLE_1M + candles_1m window.

    Expected event.data keys: high, low, close.
    """

    handler_id: str = "candle"

    def handle(
        self,
        event: MarketEvent,
        windows: SymbolWindowState,
        state: SymbolFeatureState,
    ) -> list[RawFeature]:
        features: list[RawFeature] = []
        d = event.data

        high = float(d.get("high", 0) or 0)
        low = float(d.get("low", 0) or 0)
        close = float(d.get("close", 0) or 0)

        if high > 0:
            features.append(_feature(FeatureId.HIGH_1M, high))
        if low > 0:
            features.append(_feature(FeatureId.LOW_1M, low))

        # volatility = (high - low) / close
        if high > 0 and low > 0 and close > 0:
            vol = (high - low) / close * 100.0
            features.append(_feature(FeatureId.VOLATILITY_1M, vol))

        # RSI from candles_1m close prices
        candles = list(windows.candles_1m)
        closes = [float(c.data.get("close", 0) or 0) for c in candles if c.data.get("close")]
        if close > 0:
            closes.append(close)
        rsi_val = _rsi(closes, period=14)
        features.append(_feature(FeatureId.RSI_14_1M, rsi_val))

        return features


# ── T6C: Liquidation ──

class LiquidationHandler:
    """Extract liquidation_imbalance from LIQUIDATION event.

    Expected event.data keys: long_qty, short_qty (aggregate volumes).
    Output range: -1.0 (short dominated) to +1.0 (long dominated).
    """

    handler_id: str = "liquidation"

    def handle(
        self,
        event: MarketEvent,
        windows: SymbolWindowState,
        state: SymbolFeatureState,
    ) -> list[RawFeature]:
        features: list[RawFeature] = []
        d = event.data

        long_qty = float(d.get("long_qty", 0) or 0)
        short_qty = float(d.get("short_qty", 0) or 0)
        total = long_qty + short_qty

        if total > 0:
            imbalance = (long_qty - short_qty) / total
        else:
            imbalance = 0.0

        features.append(_feature(FeatureId.LIQUIDATION_IMBALANCE, imbalance))

        return features
