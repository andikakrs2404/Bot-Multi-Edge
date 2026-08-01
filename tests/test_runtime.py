"""Tests for AlphaOS runtime artifacts (MarketSnapshot)."""

import math
from datetime import datetime, timezone

import pytest

from shared.runtime import MarketSnapshot, make_snapshot_id


def snap(features: dict[str, float], ts: datetime | None = None):
    ts = ts or datetime(2026, 7, 31, 12, 0, 0, tzinfo=timezone.utc)
    return MarketSnapshot(
        snapshot_id=make_snapshot_id("BTCUSDT", ts, features),
        symbol="BTCUSDT",
        timestamp=ts,
        feature_values=features,
    )


class TestSnapshotId:
    def test_deterministic_and_order_insensitive(self):
        a = make_snapshot_id("BTCUSDT", datetime(2026, 7, 31, tzinfo=timezone.utc),
                             {"RSI_14": 70.0, "EMA_20": 100.0})
        b = make_snapshot_id("BTCUSDT", datetime(2026, 7, 31, tzinfo=timezone.utc),
                             {"EMA_20": 100.0, "RSI_14": 70.0})
        assert a == b

    def test_changes_with_values(self):
        a = make_snapshot_id("BTCUSDT", datetime(2026, 7, 31, tzinfo=timezone.utc),
                             {"RSI_14": 70.0})
        b = make_snapshot_id("BTCUSDT", datetime(2026, 7, 31, tzinfo=timezone.utc),
                             {"RSI_14": 71.0})
        assert a != b

    def test_changes_with_symbol(self):
        a = make_snapshot_id("BTCUSDT", datetime(2026, 7, 31, tzinfo=timezone.utc),
                             {"RSI_14": 70.0})
        b = make_snapshot_id("ETHUSDT", datetime(2026, 7, 31, tzinfo=timezone.utc),
                             {"RSI_14": 70.0})
        assert a != b


class TestInvariants:
    def test_empty_features_rejected(self):
        with pytest.raises(ValueError, match="empty"):
            snap({})

    def test_blank_symbol_rejected(self):
        with pytest.raises(ValueError, match="symbol"):
            MarketSnapshot(
                snapshot_id="x",
                symbol="   ",
                timestamp=datetime(2026, 7, 31, tzinfo=timezone.utc),
                feature_values={"RSI_14": 70.0},
            )

    def test_blank_feature_name_rejected(self):
        with pytest.raises(ValueError, match="feature name"):
            snap({"": 70.0})

    def test_nan_rejected(self):
        with pytest.raises(ValueError, match="NaN|nan|finite"):
            snap({"RSI_14": math.nan})

    def test_inf_rejected(self):
        with pytest.raises(ValueError, match="finite"):
            snap({"RSI_14": math.inf})

    def test_naive_timestamp_rejected(self):
        with pytest.raises(ValueError, match="tz|timezone|aware"):
            snap({"RSI_14": 70.0}, ts=datetime(2026, 7, 31, 12, 0, 0))

    def test_roundtrip(self):
        s = snap({"RSI_14": 70.0, "EMA_20": 100.0})
        assert s.symbol == "BTCUSDT"
        assert s.feature_values == {"RSI_14": 70.0, "EMA_20": 100.0}
        assert s.snapshot_id
