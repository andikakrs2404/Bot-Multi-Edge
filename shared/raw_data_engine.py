"""AlphaOS Raw Data Engine (ADR-000B/003/004/005).

Produces ONLY Trust Level 0-1 artifacts:
Exchange API → RawObservation[] → validation → raw parquet
             → manifest.json → content_hash → Dataset → DatasetRegistry

Never produces Feature/Label/Rule/Edge (trust boundary, ADR-000B).
Spec: docs/specifications/raw-data-engine.md
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from .binance import (
    FetchStats,
    fetch_24h_volume_map,
    fetch_funding,
    fetch_klines,
    fetch_open_interest,
)
from .contracts import CONSTITUTION_HASH, Dataset, DatasetStatus, utcnow
from .registry import DuplicateActiveError, Registry
from .universe import Tier, UniverseDefinition
from .validation import (
    check_dataset_id,
    content_hash_of,
    dataset_id_of,
    validate_manifest,
    validate_raw_observation,
)

DATASET_TYPES = ("klines", "funding", "open_interest")
INTERVALS = ("30m", "1h", "4h", "1d")
MAX_INVALID_RATIO = 0.01  # spec §7: fails loud above 1%


class EngineError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class DatasetResult:
    dataset_id: str
    dataset_type: str
    path: Path
    row_count: int
    dropped_rows: int
    failed_symbols: tuple[str, ...]


class RawDataEngine:
    """Orchestrator: download → validate → artifacts → register (spec §3,§8)."""

    def __init__(self, data_root: Path, dataset_registry: Registry | None = None) -> None:
        self.data_root = Path(data_root)
        self.datasets_dir = self.data_root / "datasets"
        self.raw_dir = self.data_root / "raw"
        self.registry = dataset_registry
        self.stats = FetchStats()

    # ── pipeline ──

    def build_dataset(self, dataset_type: str, symbols: list[str],
                      start: str, end: str, interval: str = "30m",
                      universe: UniverseDefinition | None = None,
                      tiers: dict[str, Tier] | None = None) -> DatasetResult:
        """Full pipeline for one dataset type over one universe (spec §3)."""
        if dataset_type not in DATASET_TYPES:
            raise EngineError(f"unknown dataset_type: {dataset_type}")
        if interval not in INTERVALS:
            raise EngineError(f"unknown interval: {interval}")
        start_ms, end_ms = _to_ms(start), _to_ms(end)
        if start_ms >= end_ms:
            raise EngineError(f"empty range: {start} >= {end}")

        rows: list[dict] = []
        dropped = 0
        failed: list[str] = []
        for sym in symbols:
            try:
                raw = self._fetch(dataset_type, sym, interval, start_ms, end_ms)
                valid, bad = _validate_rows(raw)
                rows.extend(valid)
                dropped += bad
            except Exception as e:  # symbol-level isolation (spec §6)
                failed.append(f"{sym}: {e}")
        if not rows:
            raise EngineError(f"no valid rows for {dataset_type}")

        # write raw parquet (trust level 0)
        type_dir = self.raw_dir / dataset_type
        type_dir.mkdir(parents=True, exist_ok=True)
        table = _to_table(rows, dataset_type)
        pq.write_table(table, type_dir / f"{dataset_type}.parquet")

        # manifest + dataset_id (trust level 1, ADR-004)
        manifest = self._manifest(dataset_type, interval, start, end, rows,
                                  universe, table)
        ds_dir = self.datasets_dir / manifest["dataset_id"]
        if ds_dir.exists():
            raise EngineError(f"immutability: dataset {manifest['dataset_id'][:12]}… exists")
        ds_dir.mkdir(parents=True)
        (ds_dir / "dataset.parquet").write_bytes((ds_dir.parent.parent / "raw" / dataset_type
                                                  / f"{dataset_type}.parquet").read_bytes())
        (ds_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
        metadata = {"symbols": list({r["symbol"] for r in rows}), "universe": manifest["universe_id"]}
        if tiers is not None:
            metadata["tiers"] = {s: t.value for s, t in sorted(tiers.items())}
        (ds_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))

        # register (spec §8) — engine stops here
        dataset = Dataset(
            dataset_id=manifest["dataset_id"],
            schema_version=manifest["schema_version"],
            universe=manifest["universe_id"],
            timeframe=manifest["timeframe"],
            date_range=(manifest["period"]["start"], manifest["period"]["end"]),
            content_hash=manifest["content_hash"],
            status=DatasetStatus.REGISTERED,
        )
        if self.registry is not None:
            try:
                self.registry.register(dataset)
            except DuplicateActiveError:
                raise EngineError(f"already registered: {dataset.dataset_id[:12]}…")

        return DatasetResult(
            dataset_id=dataset.dataset_id,
            dataset_type=dataset_type,
            path=ds_dir,
            row_count=len(rows),
            dropped_rows=dropped,
            failed_symbols=tuple(failed),
        )

    # ── internals ──

    def _fetch(self, dataset_type: str, symbol: str, interval: str,
               start_ms: int, end_ms: int) -> list[dict]:
        if dataset_type == "klines":
            raw = fetch_klines(symbol, interval, start_ms, end_ms, self.stats)
            for r in raw:
                r["symbol"] = symbol
                r["exchange"] = "binance_futures"
            return raw
        if dataset_type == "funding":
            raw = fetch_funding(symbol, start_ms, end_ms, self.stats)
            for r in raw:
                r["symbol"] = symbol
                r["exchange"] = "binance_futures"
                r.update({"open": 0.0, "high": 0.0, "low": 0.0, "close": 0.0, "volume": 0.0})
            return raw
        if dataset_type == "open_interest":
            raw = fetch_open_interest(symbol, interval, start_ms, end_ms, self.stats)
            for r in raw:
                r["symbol"] = symbol
                r["exchange"] = "binance_futures"
                r.update({"open": 0.0, "high": 0.0, "low": 0.0, "close": 0.0, "volume": 0.0})
            return raw
        raise EngineError(f"unknown type {dataset_type}")

    def _manifest(self, dataset_type: str, interval: str, start: str, end: str,
                  rows: list[dict], universe: UniverseDefinition | None,
                  table: pa.Table) -> dict:
        raw_file = self.raw_dir / dataset_type / f"{dataset_type}.parquet"
        content_hash = content_hash_of(raw_file.read_bytes().hex())
        manifest = {
            "dataset_type": dataset_type,
            "source": {"exchange": "binance_futures",
                       "endpoint": _ENDPOINTS[dataset_type]},
            "period": {"start": start, "end": end},
            "date_range": [start, end],
            "timeframe": interval,
            "universe_id": universe.universe_id if universe else "adhoc",
            "schema_version": "1.0",
            "row_count": len(rows),
            "content_hash": content_hash,
            "constitution_hash": CONSTITUTION_HASH,
        }
        # created_at is provenance metadata, NOT identity — excluded from hash
        manifest["dataset_id"] = dataset_id_of(manifest)
        manifest["created_at"] = utcnow().isoformat()
        return manifest


_ENDPOINTS = {
    "klines": "/fapi/v1/klines",
    "funding": "/fapi/v1/fundingRate",
    "open_interest": "/futures/data/openInterestHist",
}


def _to_ms(iso: str) -> int:
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def _validate_rows(rows: list[dict]) -> tuple[list[dict], int]:
    valid, bad = [], 0
    for r in rows:
        result = validate_raw_observation(r)
        if result.ok:
            valid.append(r)
        else:
            bad += 1
    if bad and bad / max(len(rows), 1) > MAX_INVALID_RATIO:
        raise EngineError(f"invalid ratio {bad}/{len(rows)} > {MAX_INVALID_RATIO}")
    return valid, bad


def _to_table(rows: list[dict], dataset_type: str) -> pa.Table:
    schema = pa.schema([
        ("ts", pa.int64()),
        ("symbol", pa.string()),
        ("exchange", pa.string()),
        ("open", pa.float64()), ("high", pa.float64()), ("low", pa.float64()),
        ("close", pa.float64()), ("volume", pa.float64()),
        *((pa.field("funding_rate", pa.float64()),) if dataset_type == "funding" else ()),
        *((pa.field("open_interest", pa.float64()),) if dataset_type == "open_interest" else ()),
    ])
    cols = {name: [] for name in schema.names}
    for r in rows:
        for name in schema.names:
            cols[name].append(r.get(name))
    return pa.Table.from_arrays([pa.array(cols[n], type=schema.field(n).type)
                                 for n in schema.names], schema=schema)


def verify_dataset(ds_dir: Path) -> tuple[bool, list[str]]:
    """Re-verify a dataset artifact (spec §9): manifest + id + content hash."""
    errors: list[str] = []
    manifest = json.loads((ds_dir / "manifest.json").read_text())
    if not validate_manifest(manifest).ok:
        errors.append("manifest invalid")
    if not check_dataset_id(manifest).ok:
        errors.append("dataset_id mismatch")
    actual = content_hash_of((ds_dir / "dataset.parquet").read_bytes().hex())
    if actual != manifest["content_hash"]:
        errors.append("content_hash mismatch")
    return (not errors, errors)
