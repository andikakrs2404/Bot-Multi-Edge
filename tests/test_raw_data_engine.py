"""Tests for AlphaOS Raw Data Engine (ADR-003/004/005, spec raw-data-engine).

Mocked HTTP: no live Binance calls. Verifies trust boundary (engine never
produces Feature/Label/Rule/Edge), artifact structure, immutability,
dataset_id verification, registry integration.
"""

import json
from pathlib import Path
from unittest import mock

import pytest

from shared.binance import FetchStats, _get_json, fetch_klines
from shared.contracts import Dataset, Edge, Feature, Rule
from shared.raw_data_engine import (
    EngineError,
    RawDataEngine,
    _to_ms,
    verify_dataset,
)
from shared.registries import DatasetRegistry
from shared.universe import Tier, UniverseDefinition, build_universe, tier_of


def make_klines(n=3, start_ms=1_700_000_000_000, step=1_800_000):
    rows = []
    for i in range(n):
        t = start_ms + i * step
        o = 100.0 + i
        rows.append([t, o, o + 2, o - 1, o + 1, 1000.0, t, "0", 0, "0", "0", "0"])
    return rows


def fake_engine(tmp_path):
    return RawDataEngine(Path(tmp_path))


class TestFetchKlines:
    @mock.patch("shared.binance._get_json")
    def test_pagination_walks_start_time(self, get):
        # first batch FULL (1500 rows) forces a second page
        full = make_klines(1500, 1_700_000_000_000, 1_800_000)
        second = make_klines(2, 1_700_000_000_000 + 1500 * 1_800_000, 1_800_000)
        get.side_effect = [full, second, []]
        stats = FetchStats()
        rows = fetch_klines("BTCUSDT", "30m", 1_700_000_000_000,
                            1_700_000_000_000 + 1502 * 1_800_000, stats)
        assert len(rows) == 1502
        # cursor = last ts of full batch + 1
        assert get.call_args_list[1][0][1]["startTime"] == full[-1][0] + 1

    @mock.patch("shared.binance.urllib.request.urlopen")
    def test_retry_on_429(self, urlopen):
        import urllib.error
        from shared.binance import _get_json
        resp = mock.MagicMock()
        resp.read.return_value = b"[]"
        resp.__enter__.return_value = resp  # context manager support
        urlopen.side_effect = [urllib.error.HTTPError(
            "https://fapi.binance.com", 429, "Too Many Requests", {}, None), resp]
        stats = FetchStats()
        out = _get_json("https://fapi.binance.com/fapi/v1/klines",
                        {"symbol": "BTCUSDT"}, stats=stats)
        assert out == []
        assert stats.retries == 1
        assert urlopen.call_count == 2

    @mock.patch("shared.binance._get_json")
    def test_http_error_raises_after_retries(self, get):
        from shared.binance import FetchError
        get.side_effect = FetchError("HTTP 400")  # non-retryable
        with pytest.raises(FetchError):
            fetch_klines("BTCUSDT", "30m", 1_700_000_000_000, 1_700_000_000_000 + 1_800_000)

    def test_to_ms(self):
        assert _to_ms("2023-01-01T00:00:00Z") == 1672531200000
        assert _to_ms("2023-01-01T00:00:00") == 1672531200000  # naive treated as UTC


class TestUniverse:
    def test_build_universe_top_n(self):
        vols = {f"SYM{i}USDT": float(i) for i in range(1, 20)}
        uni = UniverseDefinition(universe_id="u1", top_n=5)
        out = build_universe(vols, uni)
        assert len(out) == 5
        assert "SYM19USDT" in out  # highest volume included

    def test_tier_boundaries(self):
        assert tier_of(150e6) == Tier.A
        assert tier_of(50e6) == Tier.B
        assert tier_of(10e6) == Tier.C
        assert tier_of(1e6) == Tier.D

    def test_stablecoin_excluded(self):
        uni = UniverseDefinition(universe_id="u1")
        assert not uni.accepts("USDCUSDT")
        assert not uni.accepts("BUSDUSDT")
        assert uni.accepts("BTCUSDT")

    def test_leveraged_tokens_excluded(self):
        uni = UniverseDefinition(universe_id="u1")
        assert not uni.accepts("BTCUPUSDT")
        assert not uni.accepts("ETHDOWNUSDT")
        assert not uni.accepts("SUSHIBEARUSDT")


class TestEnginePipeline:
    @mock.patch("shared.raw_data_engine.fetch_klines")
    def test_build_klines_dataset(self, fetch, tmp_path):
        fetch.return_value = [
            {"ts": 1_700_000_000_000, "open": 100.0, "high": 102.0,
             "low": 99.0, "close": 101.0, "volume": 1000.0,
             "symbol": "BTCUSDT", "exchange": "binance_futures"},
            {"ts": 1_700_001_800_000, "open": 101.0, "high": 103.0,
             "low": 100.0, "close": 102.0, "volume": 1100.0,
             "symbol": "BTCUSDT", "exchange": "binance_futures"},
        ]
        reg = DatasetRegistry()
        engine = RawDataEngine(Path(tmp_path), dataset_registry=reg)
        uni = UniverseDefinition(universe_id="futures_top_liquidity_v1")
        res = engine.build_dataset("klines", ["BTCUSDT"],
                                   "2023-11-14T21:00:00Z", "2023-11-14T22:00:00Z",
                                   universe=uni)
        assert res.row_count == 2
        assert res.dropped_rows == 0
        assert (res.path / "manifest.json").exists()
        assert (res.path / "dataset.parquet").exists()
        assert (res.path / "metadata.json").exists()

        # manifest content
        manifest = json.loads((res.path / "manifest.json").read_text())
        assert manifest["dataset_type"] == "klines"
        assert manifest["constitution_hash"].startswith("be37bf97")
        assert manifest["universe_id"] == "futures_top_liquidity_v1"
        assert manifest["row_count"] == 2

        # registered
        ds = reg.get(res.dataset_id)
        assert isinstance(ds, Dataset)
        assert ds.timeframe == "30m"

    @mock.patch("shared.raw_data_engine.fetch_klines")
    def test_invalid_rows_dropped(self, fetch, tmp_path):
        rows = [
            {"ts": 1_700_000_000_000 + i * 1_800_000, "open": 100.0 + i,
             "high": 102.0 + i, "low": 99.0 + i, "close": 101.0 + i,
             "volume": 1000.0, "symbol": "BTCUSDT", "exchange": "binance_futures"}
            for i in range(200)
        ]
        rows[5]["volume"] = "oops"  # 1 invalid / 200 = 0.5% < 1% → dropped, not fatal
        fetch.return_value = rows
        engine = RawDataEngine(Path(tmp_path))
        res = engine.build_dataset("klines", ["BTCUSDT"],
                                   "2023-11-14T21:00:00Z", "2023-11-14T23:00:00Z")
        assert res.row_count == 199
        assert res.dropped_rows == 1

    @mock.patch("shared.raw_data_engine.fetch_klines")
    def test_symbol_failure_isolation(self, fetch, tmp_path):
        fetch.side_effect = [
            RuntimeError("boom"),  # bad symbol
            [{"ts": 1_700_000_000_000, "open": 100.0, "high": 102.0,
              "low": 99.0, "close": 101.0, "volume": 1000.0,
              "symbol": "ETHUSDT", "exchange": "binance_futures"}],
        ]
        engine = RawDataEngine(Path(tmp_path))
        res = engine.build_dataset("klines", ["BTCUSDT", "ETHUSDT"],
                                   "2023-11-14T21:00:00Z", "2023-11-14T22:00:00Z")
        assert res.row_count == 1
        assert "BTCUSDT" in res.failed_symbols[0]

    @mock.patch("shared.raw_data_engine.fetch_klines")
    def test_no_rows_raises(self, fetch, tmp_path):
        fetch.return_value = []
        engine = RawDataEngine(Path(tmp_path))
        with pytest.raises(EngineError):
            engine.build_dataset("klines", ["BTCUSDT"],
                                 "2023-11-14T21:00:00Z", "2023-11-14T22:00:00Z")

    @mock.patch("shared.raw_data_engine.fetch_klines")
    def test_immutability_enforced(self, fetch, tmp_path):
        rows = [{"ts": 1_700_000_000_000, "open": 100.0, "high": 102.0,
                 "low": 99.0, "close": 101.0, "volume": 1000.0,
                 "symbol": "BTCUSDT", "exchange": "binance_futures"}]
        fetch.return_value = rows
        engine = RawDataEngine(Path(tmp_path))
        engine.build_dataset("klines", ["BTCUSDT"],
                             "2023-11-14T21:00:00Z", "2023-11-14T22:00:00Z")
        # same inputs → same dataset_id → second build must fail (immutability)
        with pytest.raises(EngineError):
            engine.build_dataset("klines", ["BTCUSDT"],
                                 "2023-11-14T21:00:00Z", "2023-11-14T22:00:00Z")

    def test_unknown_type_rejected(self, tmp_path):
        engine = RawDataEngine(Path(tmp_path))
        with pytest.raises(EngineError):
            engine.build_dataset("labels", ["BTCUSDT"],
                                 "2023-11-14T21:00:00Z", "2023-11-14T22:00:00Z")


class TestVerifyDataset:
    @mock.patch("shared.raw_data_engine.fetch_klines")
    def test_verify_pass_and_tamper(self, fetch, tmp_path):
        fetch.return_value = [
            {"ts": 1_700_000_000_000, "open": 100.0, "high": 102.0,
             "low": 99.0, "close": 101.0, "volume": 1000.0,
             "symbol": "BTCUSDT", "exchange": "binance_futures"},
        ]
        engine = RawDataEngine(Path(tmp_path))
        res = engine.build_dataset("klines", ["BTCUSDT"],
                                   "2023-11-14T21:00:00Z", "2023-11-14T22:00:00Z")
        ok, errs = verify_dataset(res.path)
        assert ok, errs

        # tamper with the parquet
        p = res.path / "dataset.parquet"
        p.write_bytes(p.read_bytes() + b"tampered")
        ok, errs = verify_dataset(res.path)
        assert not ok
        assert any("content_hash mismatch" in e for e in errs)


class TestTrustBoundary:
    def test_engine_never_produces_knowledge_entities(self):
        """Raw Data Engine output must contain no Feature/Label/Rule/Edge."""
        src = Path(__file__).parent.parent / "shared" / "raw_data_engine.py"
        text = src.read_text()
        for entity in ("Feature(", "Rule(", "Edge(", "Label("):
            assert entity not in text, f"engine must not produce {entity}"


class TestRegistryIntegration:
    @mock.patch("shared.raw_data_engine.fetch_klines")
    def test_register_then_immutable(self, fetch, tmp_path):
        fetch.return_value = [
            {"ts": 1_700_000_000_000, "open": 100.0, "high": 102.0,
             "low": 99.0, "close": 101.0, "volume": 1000.0,
             "symbol": "BTCUSDT", "exchange": "binance_futures"},
        ]
        reg = DatasetRegistry()
        engine = RawDataEngine(Path(tmp_path), dataset_registry=reg)
        engine.build_dataset("klines", ["BTCUSDT"],
                             "2023-11-14T21:00:00Z", "2023-11-14T22:00:00Z")
        assert len(reg.all_active()) == 1
        # duplicate registration rejected (already ACTIVE)
        from shared.registry import DuplicateActiveError
        with pytest.raises(DuplicateActiveError):
            reg.register(reg.all_active()[0].entity)
