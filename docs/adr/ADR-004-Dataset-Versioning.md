# ADR-004: Dataset Versioning

- **Layer:** 1 (Domain & Contracts)
- **Status:** Draft
- **Date:** 2026-07-29
- **Depends On:** ADR-003

## Context

Reproducibility (priority 1, ADR-001B) is impossible if datasets can change silently. Any experiment result must be re-derivable from the exact dataset it consumed. This ADR fixes how datasets are versioned, identified, and stored.

## Decision

### Identity

Every Dataset has a `DatasetID` derived from the content of its manifest:

```text
DatasetID = SHA256( manifest )
manifest  = { universe, timeframe, date_range, source_version,
              schema_version, row_count, content_hash }
```

`content_hash` = SHA256 over the sorted concatenation of file hashes (parquet files are content-addressed).

### Versioning Rules

1. **Immutability:** a registered Dataset is never modified in place.
2. **Correction = new version:** any data fix produces a new Dataset with a new `DatasetID`. The old one stays archived.
3. **Layering:** derived datasets (snapshots, features) record their parent `DatasetID`(s) in their manifest, forming a provenance DAG.
4. **Storage layout:**

```text
data/raw/{source}/{universe}/{timeframe}/{YYYY-MM}/…parquet
data/processed/{DatasetID}/manifest.json + *.parquet
```

5. **Registry:** `datasets` table in the AKB records `DatasetID`, manifest, status (CREATED → VALIDATED → REGISTERED → ACTIVE → ARCHIVED), and creation provenance.

### Access Rule

Engines declare the `DatasetID`(s) they consume in their ExperimentConfig. A ResearchCycle records every DatasetID it touched.

## Consequences

- **Positive:** Perfect reproducibility; provenance DAG; safe corrections without destroying history.
- **Negative:** Storage grows (old versions retained). Accepted — storage is cheap, reproducibility is priceless.

## Alternatives Considered

- **In-place updates:** Rejected — breaks reproducibility axiom.
- **Timestamp-only versioning:** Rejected — not content-addressable; collisions and ambiguity.

## Migration Path

None for v1.0.
