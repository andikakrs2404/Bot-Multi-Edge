"""Tests for AlphaOS Data Contract validation (ADR-003/004).

Spec: docs/specifications/contracts/snapshot.md
"""

from datetime import datetime, timezone

import pytest

from shared.validation import (
    ContractViolation,
    assert_valid,
    check_dataset_id,
    content_hash_of,
    dataset_id_of,
    validate_manifest,
    validate_raw_observation,
    verify_content_integrity,
)


def good_row(**over):
    row = {
        "ts": "2026-01-01T00:00:00Z",
        "exchange": "binance_futures",
        "symbol": "BTCUSDT",
        "open": 100.0, "high": 105.0, "low": 99.0, "close": 104.0,
        "volume": 1000.0,
    }
    row.update(over)
    return row


class TestRawObservation:
    def test_valid_row(self):
        r = validate_raw_observation(good_row())
        assert r.ok, r.errors

    def test_missing_required_field(self):
        row = good_row()
        del row["volume"]
        r = validate_raw_observation(row)
        assert not r.ok
        assert any("volume" in e for e in r.errors)

    def test_non_numeric(self):
        r = validate_raw_observation(good_row(close="NaN"))
        assert not r.ok

    def test_high_below_low(self):
        r = validate_raw_observation(good_row(high=90.0, low=100.0))
        assert not r.ok
        assert any("high < low" in e for e in r.errors)

    def test_close_outside_range(self):
        r = validate_raw_observation(good_row(close=200.0))
        assert not r.ok

    def test_naive_timestamp_rejected(self):
        r = validate_raw_observation(good_row(ts=datetime(2026, 1, 1)))
        assert not r.ok

    def test_aware_timestamp_accepted(self):
        ts = datetime(2026, 1, 1, tzinfo=timezone.utc)
        r = validate_raw_observation(good_row(ts=ts))
        assert r.ok

    def test_bad_iso_string(self):
        r = validate_raw_observation(good_row(ts="not-a-date"))
        assert not r.ok


class TestManifest:
    def test_valid_manifest(self):
        m = {"dataset_id": "a" * 64, "schema_version": "1.0",
             "universe": "top500", "timeframe": "30m",
             "date_range": ["2023-01-01", "2026-01-01"],
             "content_hash": "b" * 64}
        assert validate_manifest(m).ok

    def test_missing_field(self):
        m = {"schema_version": "1.0"}
        assert not validate_manifest(m).ok

    def test_bad_date_range(self):
        m = {"dataset_id": "a" * 64, "schema_version": "1.0",
             "universe": "u", "timeframe": "30m",
             "date_range": "2023", "content_hash": "b" * 64}
        assert not validate_manifest(m).ok

    def test_bad_content_hash_len(self):
        m = {"dataset_id": "a" * 64, "schema_version": "1.0",
             "universe": "u", "timeframe": "30m",
             "date_range": ["a", "b"], "content_hash": "short"}
        assert not validate_manifest(m).ok


class TestContentIntegrity:
    def test_content_hash_deterministic(self):
        assert content_hash_of("abc") == content_hash_of("abc")
        assert content_hash_of("abc") != content_hash_of("abd")

    def test_verify_matches(self):
        text = "some parquet bytes…"
        m = {"content_hash": content_hash_of(text)}
        assert verify_content_integrity(m, text).ok

    def test_verify_detects_tamper(self):
        m = {"content_hash": content_hash_of("original")}
        r = verify_content_integrity(m, "tampered")
        assert not r.ok
        assert "hash mismatch" in r.errors[0]

    def test_dataset_id_roundtrip(self):
        m = {"dataset_id": "", "universe": "top500", "tf": "30m"}
        assert dataset_id_of(m) == dataset_id_of(dict(m))
        # dataset_id must match computed value
        m["dataset_id"] = dataset_id_of(m)
        assert check_dataset_id(m).ok

    def test_dataset_id_mismatch_detected(self):
        m = {"dataset_id": "x" * 64, "universe": "top500"}
        assert not check_dataset_id(m).ok


class TestAssertValid:
    def test_raises_on_violation(self):
        with pytest.raises(ContractViolation):
            assert_valid(validate_raw_observation(good_row(close="oops")), "row")

    def test_passes_on_valid(self):
        assert_valid(validate_raw_observation(good_row()), "row")
