"""AlphaOS Feature Factory (ADR-000B/002/003/005, spec feature-factory).

Dataset (L1) + registered FeatureIDs → FeatureSnapshot parquet (L2)
→ manifest → snapshot_id → register in DatasetRegistry (lineage parent).

NEVER produces Rule/Edge/Evidence (trust boundary, ADR-000B).
"""

from __future__ import annotations

import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from .contracts import CONSTITUTION_HASH, Dataset, DatasetStatus, utcnow
from .features import compute_feature, compute_label
from .registry import DuplicateActiveError, Registry
from .validation import content_hash_of, dataset_id_of, validate_manifest

FEATURE_COLUMNS = {
    "RSI_14_CLOSE", "EMA_20_SLOPE", "ATR_14_PCT", "VOL_Z_20", "RET_1H",
    "CANDLE_BODY", "CANDLE_UPPER_WICK", "CANDLE_LOWER_WICK", "RANGE_EXPANSION",
    "OIPCT_1H", "FUNDING_Z_20",
}
LABEL_COLUMNS = {"FWD_RET_24H", "TIME_TO_TP_SL", "FIRST_EVENT", "HIT_TARGET"}


class FeatureFactoryError(RuntimeError):
    pass


class FeatureFactory:
    """Builds FeatureSnapshots (trust level 2) from registered datasets."""

    def __init__(self, data_root: Path, dataset_registry: Registry | None = None,
                 feature_registry: Registry | None = None,
                 label_registry: Registry | None = None) -> None:
        self.data_root = Path(data_root)
        self.snapshots_dir = self.data_root / "features"
        self.dataset_registry = dataset_registry
        self.feature_registry = feature_registry
        self.label_registry = label_registry

    def build_snapshot(self, dataset_id: str, feature_ids: list[str],
                       label_ids: list[str] | None = None,
                       include_labels: bool = False,
                       tier_map: dict[str, str] | None = None) -> str:
        """Build a FeatureSnapshot from a registered dataset. Returns snapshot_id.

        - dataset must exist on disk (data/datasets/<dataset_id>)
        - every feature_id must be registered ACTIVE (ADR-005)
        - labels only when include_labels=True (research)
        """
        ds_dir = self.data_root / "datasets" / dataset_id
        if not ds_dir.exists():
            raise FeatureFactoryError(f"dataset not on disk: {dataset_id[:12]}…")
        manifest = json.loads((ds_dir / "manifest.json").read_text())
        if not validate_manifest(manifest).ok:
            raise FeatureFactoryError(f"source dataset manifest invalid: {dataset_id[:12]}…")

        # registry gate (ADR-005) — fail closed
        if self.feature_registry is None:
            raise FeatureFactoryError("feature_registry required (ADR-005)")
        for fid in feature_ids:
            if fid not in FEATURE_COLUMNS:
                raise FeatureFactoryError(f"unknown feature_id: {fid}")
            self.feature_registry.get(f"FEAT-{fid}")  # raises if not ACTIVE
        labels = label_ids or []
        for lid in labels:
            if lid not in LABEL_COLUMNS:
                raise FeatureFactoryError(f"unknown label_id: {lid}")
            if not include_labels:
                raise FeatureFactoryError(f"labels require include_labels=True: {lid}")
            if self.label_registry is None:
                raise FeatureFactoryError("label_registry required for labels (ADR-005)")
            self.label_registry.get(f"LAB-{lid}")

        # load source
        table = pq.read_table(ds_dir / "dataset.parquet")
        data = table.to_pylist()

        # group by symbol
        by_symbol: dict[str, list[dict]] = {}
        for row in data:
            by_symbol.setdefault(row["symbol"], []).append(row)

        rows: list[dict] = []
        for symbol, bars in sorted(by_symbol.items()):
            bars.sort(key=lambda r: r["ts"])
            ohlcv = {k: [b[k] for b in bars] for k in ("open", "high", "low", "close", "volume")}
            series: dict[str, list[float]] = {}
            for fid in feature_ids:
                series[fid] = compute_feature(fid, ohlcv)
            if include_labels:
                for lid in labels:
                    series[f"label_{lid}"] = label_series_flat(lid, ohlcv)
            for i, bar in enumerate(bars):
                row = {"ts": bar["ts"], "symbol": symbol,
                       "exchange": bar.get("exchange", "binance_futures"),
                       "tier": (tier_map or {}).get(symbol, "")}
                for fid in feature_ids:
                    row[fid] = series[fid][i]
                if include_labels:
                    for lid in labels:
                        row[f"label_{lid}"] = series[f"label_{lid}"][i]
                rows.append(row)

        rows.sort(key=lambda r: (r["symbol"], r["ts"]))

        # write snapshot
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)
        snapshot_meta = {
            "dataset_id": dataset_id,
            "feature_ids": feature_ids,
            "label_ids": labels,
            "universe_id": manifest.get("universe_id", "adhoc"),
            "schema_version": "1.0",
            "row_count": len(rows),
            "constitution_hash": CONSTITUTION_HASH,
        }
        snap_id = dataset_id_of(snapshot_meta)
        snap_dir = self.snapshots_dir / snap_id
        if snap_dir.exists():
            raise FeatureFactoryError(f"immutability: snapshot {snap_id[:12]}… exists")
        snap_dir.mkdir(parents=True)

        col_names = ["ts", "symbol", "exchange", "tier"] + feature_ids + \
                    [f"label_{l}" for l in labels]
        col_types = [pa.int64(), pa.string(), pa.string(), pa.string()] + \
                    [pa.float64()] * (len(feature_ids) + len(labels))
        schema = pa.schema(list(zip(col_names, col_types)))
        arrays = [pa.array([r[c] for r in rows], type=t) for c, t in zip(col_names, col_types)]
        out = pa.Table.from_arrays(arrays, schema=schema)
        pq.write_table(out, snap_dir / "snapshot.parquet")

        # manifest
        m = dict(snapshot_meta)
        m["snapshot_id"] = snap_id
        m["content_hash"] = content_hash_of((snap_dir / "snapshot.parquet").read_bytes().hex())
        m["created_at"] = utcnow().isoformat()
        (snap_dir / "manifest.json").write_text(json.dumps(m, indent=2))

        # register as feature_snapshot dataset with lineage (ADR-004)
        if self.dataset_registry is not None:
            ds = Dataset(
                dataset_id=snap_id,
                schema_version="1.0",
                universe=manifest.get("universe_id", "adhoc"),
                timeframe=manifest.get("timeframe", ""),
                date_range=(str(min(r["ts"] for r in rows)), str(max(r["ts"] for r in rows))),
                content_hash=m["content_hash"],
                parent_ids=(dataset_id,),
                status=DatasetStatus.REGISTERED,
            )
            try:
                self.dataset_registry.register(ds)
            except DuplicateActiveError:
                raise FeatureFactoryError(f"already registered: {snap_id[:12]}…") from None
        return snap_id


def label_series_flat(label_id: str, ohlcv: dict) -> list[float]:
    """Compute a flat label series from OHLCV (research)."""
    from .features import compute_label
    res = compute_label(label_id, ohlcv["close"], ohlcv["high"], ohlcv["low"])
    return res[label_id]
