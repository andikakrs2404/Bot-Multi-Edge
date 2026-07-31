"""Binance Futures fetcher (Raw Data Engine input layer).

Stdlib only: urllib for HTTP, no external client. Retry with exponential
backoff, pagination by startTime, symbol-level failure isolation.
Spec: docs/specifications/raw-data-engine.md §6.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = "https://fapi.binance.com"

KLINES_LIMIT = 1500  # Binance max per request
MS = 1000
HOUR_MS = 3600_000


class FetchError(RuntimeError):
    """Non-retryable fetch failure."""


class FetchStats:
    def __init__(self) -> None:
        self.requests = 0
        self.retries = 0
        self.dropped_rows = 0
        self.failed_symbols: list[str] = []


def _get_json(url: str, params: dict, timeout: float = 30.0,
              retries: int = 3, backoff: float = 1.0, stats: FetchStats | None = None) -> list:
    """GET with retry + exponential backoff (429/5xx retryable)."""
    qs = urllib.parse.urlencode(params)
    full = f"{url}?{qs}"
    attempt = 0
    while True:
        attempt += 1
        if stats:
            stats.requests += 1
        try:
            with urllib.request.urlopen(full, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (429, 418, 500, 502, 503, 504) and attempt <= retries:
                if stats:
                    stats.retries += 1
                time.sleep(backoff * (2 ** (attempt - 1)))
                continue
            raise FetchError(f"HTTP {e.code} for {params}") from e
        except urllib.error.URLError as e:
            if attempt <= retries:
                if stats:
                    stats.retries += 1
                time.sleep(backoff * (2 ** (attempt - 1)))
                continue
            raise FetchError(f"network error: {e.reason}") from e


def fetch_klines(symbol: str, interval: str, start_ms: int, end_ms: int,
                 stats: FetchStats | None = None) -> list[dict]:
    """All klines in [start_ms, end_ms), paginated by startTime (spec §6)."""
    out: list[dict] = []
    cursor = start_ms
    while cursor < end_ms:
        batch = _get_json(
            f"{BASE_URL}/fapi/v1/klines",
            {"symbol": symbol, "interval": interval,
             "startTime": cursor, "endTime": end_ms, "limit": KLINES_LIMIT},
            stats=stats,
        )
        if not batch:
            break
        for k in batch:
            out.append({
                "ts": k[0], "open": float(k[1]), "high": float(k[2]),
                "low": float(k[3]), "close": float(k[4]), "volume": float(k[5]),
            })
        cursor = batch[-1][0] + 1  # next open time
        if len(batch) < KLINES_LIMIT:
            break  # exhausted
        time.sleep(0.5)  # rate-limit budget
    return out


def fetch_funding(symbol: str, start_ms: int, end_ms: int,
                  stats: FetchStats | None = None) -> list[dict]:
    """Funding rate history, paginated by startTime."""
    out: list[dict] = []
    cursor = start_ms
    while cursor < end_ms:
        batch = _get_json(
            f"{BASE_URL}/fapi/v1/fundingRate",
            {"symbol": symbol, "startTime": cursor, "endTime": end_ms, "limit": 1000},
            stats=stats,
        )
        if not batch:
            break
        for f in batch:
            out.append({"ts": f["fundingTime"], "funding_rate": float(f["fundingRate"])})
        cursor = batch[-1]["fundingTime"] + 1
        if len(batch) < 1000:
            break
        time.sleep(0.5)
    return out


def fetch_open_interest(symbol: str, interval: str, start_ms: int, end_ms: int,
                        stats: FetchStats | None = None) -> list[dict]:
    """OI history (futures data endpoint), paginated by startTime."""
    out: list[dict] = []
    cursor = start_ms
    while cursor < end_ms:
        batch = _get_json(
            f"{BASE_URL}/futures/data/openInterestHist",
            {"symbol": symbol, "period": interval, "startTime": cursor,
             "endTime": end_ms, "limit": 500},
            stats=stats,
        )
        if not batch:
            break
        for o in batch:
            out.append({"ts": o["timestamp"], "open_interest": float(o["sumOpenInterestValue"])})
        cursor = batch[-1]["timestamp"] + 1
        if len(batch) < 500:
            break
        time.sleep(0.5)
    return out


def fetch_24h_volume_map(stats: FetchStats | None = None) -> dict[str, float]:
    """{symbol: quoteVolume} from /fapi/v1/ticker/24hr (universe builder input)."""
    tickers = _get_json(f"{BASE_URL}/fapi/v1/ticker/24hr", {}, stats=stats)
    return {t["symbol"]: float(t["quoteVolume"]) for t in tickers if t["symbol"].endswith("USDT")}
