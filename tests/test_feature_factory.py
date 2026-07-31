"""Tests for AlphaOS Feature Factory (ADR-002/003/005, spec feature-factory)."""

import json
import math
from pathlib import Path
from unittest import mock

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from shared.feature_factory import FeatureFactory, FeatureFactoryError
from shared.features import (
    atr_percent,
    compute_feature,
    compute_label,
    ema,
    label_series,
    rsi,
    slope_normalized,
    zscore_rolling,
)
from shared.registries import DatasetRegistry, FeatureRegistry
from shared.contracts import Dataset, Feature, DatasetStatus


# ── feature math ──

class TestFeatureMath:
    def test_ema_seed_and_trend(self):
        e = ema([1.0, 2.0, 3.0, 4.0], 3)
        assert e[0] == 1.0
        assert e[-1] > 3.0  # rising series → EMA above mid

    def test_rsi_hand_computed(self):
        # 15 closes rising monotonically → RSI = 100
        closes = [float(i) for i in range(16)]
        r = rsi(closes, 14)
        assert r[14] == 100.0
        assert all(math.isnan(v) for v in r[:14])

    def test_rsi_flat_series_50(self):
        closes = [10.0] * 20
        r = rsi(closes, 14)
        assert r[14] == 50.0

    def test_atr_percent_warmup(self):
        h = [11.0] * 20
        l = [9.0] * 20
        c = [10.0] * 20
        a = atr_percent(h, l, c, 14)
        assert math.isnan(a[0])
        # TR = 2 constant → ATR = 2 → /close 10 = 0.2
        assert a[14] == pytest.approx(0.2)

    def test_zscore_rolling(self):
        vals = [1.0, 2.0] * 10 + [20.0] + [1.0, 2.0] * 10
        z = zscore_rolling(vals, 20)
        assert math.isnan(z[18])
        assert z[20] > 3.0  # 20.0 is outlier vs mean ~1.5, sd ~0.5

    def test_compute_feature_unknown(self):
        with pytest.raises(KeyError):
            compute_feature("NOPE", {"open": [], "high": [], "low": [],
                                     "close": [], "volume": []})

    def test_slope_normalized(self):
        closes = [float(i) for i in range(30)]
        s = slope_normalized(closes, 5, scale=closes)
        assert not math.isnan(s[29])
        assert s[29] > 0  # rising


class TestLabels:
    def test_fwd_ret(self):
        closes = [100.0 + i for i in range(50)]
        lab = label_series("FWD_RET_24H", closes, closes, closes)
        assert math.isnan(lab[0])  # needs 48 bars forward
        assert lab[48] == pytest.approx(48.0 / 100.0)  # close[96]/close[48]-1
        assert lab[49] == pytest.approx(149.0 / 101.0 - 1.0)  # close[49]/close[1]-1

    def test_first_event_tp(self):
        # TP hit within horizon: spike up beyond +2% at bar 2
        closes = [100.0] * 10 + [103.0] * 10
        high = [100.0, 100.0, 105.0] + [103.0] * 17
        low = [100.0] * 10 + [99.0] * 10
        lab = label_series("FIRST_EVENT", closes, high, low, horizon=5, tp_pct=0.02)
        assert lab[0] == 1.0  # TP hit at bar 2 (high 105 ≥ 102)

    def test_first_event_sl(self):
        # SL hit within horizon: drop below -2% at bar 2
        closes = [100.0] * 10 + [97.0] * 10
        high = [100.0] * 10 + [99.0] * 10
        low = [100.0, 100.0, 95.0] + [97.0] * 17
        lab = label_series("FIRST_EVENT", closes, high, low, horizon=5, sl_pct=0.02)
        assert lab[0] == -1.0

    def test_hit_target_none(self):
        closes = [100.0] * 10
        lab = label_series("HIT_TARGET", closes, closes, closes, horizon=5,
                           tp_pct=0.02, sl_pct=0.02)
        assert lab[0] == 0.0

    def test_unknown_label(self):
        with pytest.raises(KeyError):
            compute_label("NOPE", [], [], [])


# ── factory pipeline ──

def seed_dataset(tmp_path, n_bars=60, symbols=("BTCUSDT", "ETHUSDT")):
    """Create a minimal registered klines dataset on disk."""
    rows = []
    for sym in symbols:
        for i in range(n_bars):
            ts = 1_700_000_000_000 + i * 1_800_000
            rows.append({"ts": ts, "symbol": sym, "exchange": "binance_futures",
                         "open": 100.0 + i * 0.1, "high": 102.0 + i * 0.1,
                         "low": 99.0 + i * 0.1, "close": 101.0 + i * 0.1,
                         "volume": 1000.0 + i})
    schema = pa.schema([
        ("ts", pa.int64()), ("symbol", pa.string()), ("exchange", pa.string()),
        ("open", pa.float64()), ("high", pa.float64()), ("low", pa.float64()),
        ("close", pa.float64()), ("volume", pa.float64()),
    ])
    t = pa.Table.from_arrays(
        [pa.array([r[k] for r in rows]) for k in schema.names], schema=schema)
    ds_dir = tmp_path / "datasets" / ("d" * 64)
    ds_dir.mkdir(parents=True)
    pq.write_table(t, ds_dir / "dataset.parquet")
    manifest = {"dataset_id": "d" * 64, "schema_version": "1.0",
                "universe": "u1", "timeframe": "30m",
                "date_range": ["2023", "2026"], "content_hash": "c" * 64}
    (ds_dir / "manifest.json").write_text(json.dumps(manifest))
    return "d" * 64


def make_registry():
    reg = DatasetRegistry()
    reg.register(Dataset(dataset_id="d" * 64, schema_version="1.0", universe="u1",
                         timeframe="30m", date_range=("2023", "2026"),
                         content_hash="c" * 64, status=DatasetStatus.REGISTERED))
    return reg


class TestFactory:
    def test_build_snapshot(self, tmp_path):
        did = seed_dataset(tmp_path)
        ds_reg = make_registry()
        feat_reg = FeatureRegistry()
        feat_reg.register(Feature(feature_id="FEAT-RSI_14_CLOSE"))
        f = FeatureFactory(tmp_path, dataset_registry=ds_reg, feature_registry=feat_reg)
        snap_id = f.build_snapshot(did, ["RSI_14_CLOSE"])
        snap_dir = tmp_path / "features" / snap_id
        assert (snap_dir / "snapshot.parquet").exists()
        assert (snap_dir / "manifest.json").exists()
        m = json.loads((snap_dir / "manifest.json").read_text())
        assert m["snapshot_id"] == snap_id
        assert m["dataset_id"] == did
        assert m["constitution_hash"].startswith("be37bf97")
        # registered with lineage
        ds = ds_reg.get(snap_id)
        assert ds.parent_ids == (did,)

    def test_unregistered_feature_rejected(self, tmp_path):
        did = seed_dataset(tmp_path)
        ds_reg = make_registry()
        f = FeatureFactory(tmp_path, dataset_registry=ds_reg)
        with pytest.raises(FeatureFactoryError):
            f.build_snapshot(did, ["RSI_14_CLOSE"])  # not registered

    def test_unknown_feature_rejected(self, tmp_path):
        did = seed_dataset(tmp_path)
        f = FeatureFactory(tmp_path)
        with pytest.raises(FeatureFactoryError):
            f.build_snapshot(did, ["NOPE"])

    def test_labels_require_flag(self, tmp_path):
        did = seed_dataset(tmp_path)
        ds_reg = make_registry()
        feat_reg = FeatureRegistry()
        lab_reg = FeatureRegistry()
        feat_reg.register(Feature(feature_id="FEAT-RSI_14_CLOSE"))
        lab_reg.register(Feature(feature_id="LAB-FWD_RET_24H", kind="label"))
        f = FeatureFactory(tmp_path, dataset_registry=ds_reg,
                           feature_registry=feat_reg, label_registry=lab_reg)
        with pytest.raises(FeatureFactoryError):
            f.build_snapshot(did, ["RSI_14_CLOSE"], label_ids=["FWD_RET_24H"])

    def test_labels_included_with_flag(self, tmp_path):
        did = seed_dataset(tmp_path)
        ds_reg = make_registry()
        feat_reg = FeatureRegistry()
        lab_reg = FeatureRegistry()
        feat_reg.register(Feature(feature_id="FEAT-RSI_14_CLOSE"))
        lab_reg.register(Feature(feature_id="LAB-FWD_RET_24H", kind="label"))
        f = FeatureFactory(tmp_path, dataset_registry=ds_reg,
                           feature_registry=feat_reg, label_registry=lab_reg)
        snap_id = f.build_snapshot(did, ["RSI_14_CLOSE"],
                                   label_ids=["FWD_RET_24H"], include_labels=True)
        t = pq.read_table(tmp_path / "features" / snap_id / "snapshot.parquet")
        assert "label_FWD_RET_24H" in t.column_names

    def test_missing_dataset_rejected(self, tmp_path):
        f = FeatureFactory(tmp_path)
        with pytest.raises(FeatureFactoryError):
            f.build_snapshot("z" * 64, ["RSI_14_CLOSE"])

    def test_immutability(self, tmp_path):
        did = seed_dataset(tmp_path)
        ds_reg = make_registry()
        feat_reg = FeatureRegistry()
        feat_reg.register(Feature(feature_id="FEAT-RSI_14_CLOSE"))
        f = FeatureFactory(tmp_path, dataset_registry=ds_reg, feature_registry=feat_reg)
        f.build_snapshot(did, ["RSI_14_CLOSE"])
        with pytest.raises(FeatureFactoryError):
            f.build_snapshot(did, ["RSI_14_CLOSE"])


class TestTrustBoundary:
    def test_factory_never_produces_rules_edges(self):
        src = Path(__file__).parent.parent / "shared" / "feature_factory.py"
        text = src.read_text()
        for entity in ("Rule(", "Edge(", "Evidence("):
            assert entity not in text, f"factory must not produce {entity}"
