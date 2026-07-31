"""AlphaOS feature & label computation (ADR-002/005, spec feature-factory §4-5).

Pure per-symbol math over OHLCV arrays. Deterministic, no cross-sectional
leakage. Feature identity comes from the registry, not from this module.
"""

from __future__ import annotations

import math

# ── helpers ──


def ema(values: list[float], period: int) -> list[float]:
    """Exponential moving average (seed = first value)."""
    if not values:
        return []
    alpha = 2.0 / (period + 1)
    out = [values[0]]
    for v in values[1:]:
        out.append(alpha * v + (1 - alpha) * out[-1])
    return out


def rsi(close: list[float], period: int = 14) -> list[float]:
    """Wilder RSI. First `period` values NaN (warmup)."""
    if len(close) < period + 1:
        return [math.nan] * len(close)
    out: list[float] = []
    gains: list[float] = []
    losses: list[float] = []
    for i in range(1, len(close)):
        ch = close[i] - close[i - 1]
        gains.append(max(ch, 0.0))
        losses.append(max(-ch, 0.0))
    # seed average
    avg_g = sum(gains[:period]) / period
    avg_l = sum(losses[:period]) / period
    for i in range(period):
        out.append(math.nan)
    if avg_g == 0 and avg_l == 0:
        out.append(50.0)  # flat series convention
    elif avg_l == 0:
        out.append(100.0)
    else:
        out.append(100.0 - 100.0 / (1 + avg_g / avg_l))
    for i in range(period, len(gains)):
        avg_g = (avg_g * (period - 1) + gains[i]) / period
        avg_l = (avg_l * (period - 1) + losses[i]) / period
        if avg_g == 0 and avg_l == 0:
            out.append(50.0)
        elif avg_l == 0:
            out.append(100.0)
        else:
            out.append(100.0 - 100.0 / (1 + avg_g / avg_l))
    return out


def atr_percent(high: list[float], low: list[float], close: list[float],
                period: int = 14) -> list[float]:
    """ATR(period)/close. NaN during warmup."""
    n = len(close)
    if n < period + 1:
        return [math.nan] * n
    trs: list[float] = []
    for i in range(1, n):
        trs.append(max(high[i] - low[i],
                       abs(high[i] - close[i - 1]),
                       abs(low[i] - close[i - 1])))
    out: list[float] = [math.nan]  # first bar has no TR
    seed = sum(trs[:period]) / period
    # ATR at bar `period` (index = period)
    while len(out) < period:
        out.append(math.nan)
    out.append(seed / close[period] if close[period] else math.nan)
    prev = seed
    for i in range(period, len(trs)):
        prev = (prev * (period - 1) + trs[i]) / period
        out.append(prev / close[i + 1] if close[i + 1] else math.nan)
    return out


def zscore_rolling(values: list[float], period: int = 20) -> list[float]:
    """Rolling z-score. NaN while window not full."""
    out: list[float] = []
    for i in range(len(values)):
        if i < period:
            out.append(math.nan)
            continue
        window = values[i - period:i]
        mean = sum(window) / period
        var = sum((v - mean) ** 2 for v in window) / period
        sd = math.sqrt(var)
        out.append(0.0 if sd == 0 else (values[i] - mean) / sd)
    return out


def pct_change(values: list[float], k: int = 1) -> list[float]:
    out: list[float] = []
    for i in range(len(values)):
        if i < k or values[i - k] == 0:
            out.append(math.nan)
        else:
            out.append(values[i] / values[i - k] - 1.0)
    return out


def slope_normalized(values: list[float], period: int = 20,
                     scale: list[float] | None = None) -> list[float]:
    """EMA slope over `period` bars, normalized (per bar, % of base)."""
    e = ema(values, period)
    out: list[float] = []
    for i in range(len(e)):
        if i < period:
            out.append(math.nan)
            continue
        base = scale[i] if scale else e[i - period]
        out.append((e[i] - e[i - period]) / period / base if base else math.nan)
    return out


# ── feature computes (spec §4) ──

def compute_feature(feature_id: str, ohlcv: dict) -> list[float]:
    """Compute one feature series from OHLCV dict {open,high,low,close,volume}.

    Registry version lives in FeatureRegistry; this maps FeatureID → math.
    """
    o, h, l, c, v = ohlcv["open"], ohlcv["high"], ohlcv["low"], ohlcv["close"], ohlcv["volume"]
    n = len(c)
    if feature_id == "RSI_14_CLOSE":
        return rsi(c, 14)
    if feature_id == "EMA_20_SLOPE":
        return slope_normalized(c, 20, scale=c)
    if feature_id == "ATR_14_PCT":
        return atr_percent(h, l, c, 14)
    if feature_id == "VOL_Z_20":
        return zscore_rolling(v, 20)
    if feature_id == "RET_1H":
        return pct_change(c, 2)
    if feature_id == "CANDLE_BODY":
        rng = [hi - lo if hi > lo else math.nan for hi, lo in zip(h, l)]
        return [(cl - op) / rg if rg else math.nan
                for cl, op, rg in zip(c, o, rng)]
    if feature_id == "CANDLE_UPPER_WICK":
        rng = [hi - lo if hi > lo else math.nan for hi, lo in zip(h, l)]
        return [(hi - max(cl, op)) / rg if rg else math.nan
                for hi, cl, op, rg in zip(h, c, o, rng)]
    if feature_id == "CANDLE_LOWER_WICK":
        rng = [hi - lo if hi > lo else math.nan for hi, lo in zip(h, l)]
        return [(min(cl, op) - lo) / rg if rg else math.nan
                for cl, op, lo, rg in zip(c, o, l, rng)]
    if feature_id == "RANGE_EXPANSION":
        rng = [hi - lo if hi > lo else 0.0 for hi, lo in zip(h, l)]
        base = ema(rng, 20)
        return [r / b if b else math.nan for r, b in zip(rng, base)]
    raise KeyError(f"unknown feature_id: {feature_id}")


# ── label computes (spec §5) ──

def compute_label(label_id: str, close: list[float], high: list[float],
                  low: list[float], horizon: int = 48,
                  tp_pct: float = 0.02, sl_pct: float = 0.02) -> dict:
    """Compute label series. Returns {label_id: [values]}.

    Horizon in bars (30m bars, 24h = 48). Forward-looking by definition —
    research datasets only.
    """
    n = len(close)
    if label_id == "FWD_RET_24H":
        return {label_id: pct_change(close, horizon)}
    if label_id in ("TIME_TO_TP_SL", "FIRST_EVENT", "HIT_TARGET"):
        ttp: list[float] = []
        tts: list[float] = []
        first: list[float] = []
        hit: list[float] = []
        for i in range(n):
            tp_i = sl_i = math.nan
            ev = 0.0  # 0=none, 1=tp, -1=sl
            h = 0.0   # 0/1
            for j in range(i + 1, min(i + 1 + horizon, n)):
                if high[j] >= close[i] * (1 + tp_pct):
                    tp_i = j - i
                    ev = 1.0
                    h = 1.0
                    break
                if low[j] <= close[i] * (1 - sl_pct):
                    sl_i = j - i
                    ev = -1.0
                    break
            ttp.append(tp_i)
            tts.append(sl_i)
            first.append(ev)
            hit.append(h)
        return {label_id: {"TIME_TO_TP_SL": ttp, "FIRST_EVENT": first,
                           "HIT_TARGET": hit}[label_id]}
    raise KeyError(f"unknown label_id: {label_id}")


def label_series(label_id: str, close: list[float], high: list[float],
                 low: list[float], horizon: int = 48,
                 tp_pct: float = 0.02, sl_pct: float = 0.02) -> list[float]:
    """Single label series (flat)."""
    return compute_label(label_id, close, high, low, horizon, tp_pct, sl_pct)[label_id]
