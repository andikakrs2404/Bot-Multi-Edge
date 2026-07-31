"""AlphaOS Data Contract validation (ADR-003).

Validators for Raw Observations (trust level 0), Dataset manifests,
and content integrity. Spec: docs/specifications/contracts/snapshot.md
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone

REQUIRED_RAW_FIELDS = ("ts", "exchange", "symbol", "open", "high", "low", "close", "volume")
NUMERIC_RAW_FIELDS = ("open", "high", "low", "close", "volume")
MANIFEST_REQUIRED = ("dataset_id", "schema_version", "universe", "timeframe",
                     "date_range", "content_hash")


class ContractViolation(ValueError):
    """A data artifact violates its contract."""


@dataclass(frozen=True, slots=True)
class ValidationResult:
    ok: bool
    errors: tuple[str, ...] = ()


def validate_raw_observation(row: dict) -> ValidationResult:
    """Validate one raw observation row (trust level 0)."""
    errors = []
    for f in REQUIRED_RAW_FIELDS:
        if f not in row or row[f] is None:
            errors.append(f"missing required field: {f}")
    for f in NUMERIC_RAW_FIELDS:
        if f in row and row[f] is not None and not isinstance(row[f], (int, float)):
            errors.append(f"field {f} not numeric: {row[f]!r}")
    if "ts" in row and row["ts"] is not None:
        ts = row["ts"]
        if isinstance(ts, str):
            try:
                datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except ValueError:
                errors.append(f"ts not ISO8601: {ts!r}")
        elif isinstance(ts, datetime):
            if ts.tzinfo is None:
                errors.append("ts must be timezone-aware (UTC)")
    # sanity: high >= low, close within [low, high]
    try:
        if row["high"] < row["low"]:
            errors.append("high < low")
        if not (row["low"] <= row["close"] <= row["high"]):
            errors.append("close outside [low, high]")
    except (KeyError, TypeError):
        pass  # missing fields already reported
    return ValidationResult(ok=not errors, errors=tuple(errors))


def validate_manifest(manifest: dict) -> ValidationResult:
    """Validate a dataset manifest (ADR-004)."""
    errors = []
    for f in MANIFEST_REQUIRED:
        if f not in manifest:
            errors.append(f"manifest missing field: {f}")
    if "date_range" in manifest:
        dr = manifest["date_range"]
        if not (isinstance(dr, (list, tuple)) and len(dr) == 2):
            errors.append("date_range must be [start, end]")
    if "content_hash" in manifest and len(manifest["content_hash"]) != 64:
        errors.append("content_hash must be 64 hex chars (sha256)")
    return ValidationResult(ok=not errors, errors=tuple(errors))


def content_hash_of(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def verify_content_integrity(manifest: dict, actual_text: str) -> ValidationResult:
    """Verify file content matches the manifest content_hash (ADR-004)."""
    if "content_hash" not in manifest:
        return ValidationResult(ok=False, errors=("no content_hash in manifest",))
    actual = content_hash_of(actual_text)
    if actual != manifest["content_hash"]:
        return ValidationResult(
            ok=False,
            errors=(f"content hash mismatch: manifest={manifest['content_hash'][:12]}… "
                    f"actual={actual[:12]}…",),
        )
    return ValidationResult(ok=True)


def dataset_id_of(manifest: dict) -> str:
    """Deterministic DatasetID = SHA256(canonical manifest without
    the self-referential dataset_id field) (ADR-004)."""
    body = {k: v for k, v in manifest.items() if k != "dataset_id"}
    canonical = json.dumps(body, sort_keys=True, default=str)
    return content_hash_of(canonical)


def check_dataset_id(manifest: dict) -> ValidationResult:
    """Verify manifest.dataset_id matches the canonical computation."""
    expected = dataset_id_of(manifest)
    if manifest.get("dataset_id") != expected:
        return ValidationResult(
            ok=False,
            errors=(f"dataset_id mismatch: manifest={manifest.get('dataset_id')} "
                    f"computed={expected}",),
        )
    return ValidationResult(ok=True)


def assert_valid(result: ValidationResult, what: str = "artifact") -> None:
    """Raise ContractViolation unless result.ok."""
    if not result.ok:
        raise ContractViolation(f"{what} failed: " + "; ".join(result.errors))
