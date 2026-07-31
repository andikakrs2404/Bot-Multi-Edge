# Specification: Raw Data Engine

Derived from: ADR-000B (Trust Model), ADR-003 (Data Contract), ADR-004 (Dataset Versioning), ADR-005 (Registry Model)
Constitution: be37bf97... (Freeze v1.0, 2026-07-29)

Status: Draft (v0.1)

## 1. Scope Boundary

The Raw Data Engine produces **only Trust Level 0 and Level 1 artifacts** (ADR-000B):

```text
Exchange API → RawObservation[] → validation → raw parquet
           → manifest.json → content_hash → Dataset → DatasetRegistry
```

It NEVER produces Feature, Label, Rule, or Edge. Those belong to higher trust levels (ADR-000B, ADR-002).

## 2. Inputs

| Input | Source |
| --- | --- |
| Exchange | Binance Futures (USDT-margined perpetuals) |
| Universe | `UniverseDefinition` artifact (top-N by volume + tier tags) |
| Time range | `[start, end]` UTC |
| Data types | klines (OHLCV), funding rate, open interest |

## 3. Outputs (artifacts)

```text
data/raw/<type>/<symbol>.parquet          # validated raw observations
data/datasets/<dataset_id>/
    manifest.json                         # ADR-004 manifest
    dataset.parquet                       # concatenated, sorted by (symbol, ts)
    metadata.json                         # universe + tier tagging + provenance
```

`dataset_id` addresses the artifacts — immutable content (ADR-004).

## 4. Universe Definition (artifact, not hardcoded)

```yaml
universe_id: futures_top_liquidity_v1
selection:
  metric: volume_usdt_24h
  top_n: 500
  exclude: [stablecoin pairs, leveraged tokens]
rebalance: weekly
```

- Universe is a **separate reproducible artifact**, never hardcoded in the engine.
- Tier is **dataset metadata** (characteristic of the universe), not a feature:

```json
{ "symbol": "SOLUSDT", "tier": "A" }
```

| Tier | 24h volume (USDT) |
| --- | --- |
| A | > 100M |
| B | 20M – 100M |
| C | 5M – 20M |
| D | < 5M |

## 5. Manifest (minimal)

```yaml
dataset_id:        # SHA256 of manifest body (excludes dataset_id itself)
dataset_type:      # klines | funding | open_interest
source:
  exchange: binance_futures
  endpoint: /fapi/v1/klines
period: { start, end }
universe_id: futures_top_liquidity_v1
row_count: 123456
content_hash:      # SHA256 of the parquet file bytes
constitution_hash: # be37bf97... (under which this dataset was produced)
created_at:        # UTC
```

## 6. Downloader Requirements

- Pagination (Binance klines limit 1500/request; walk by startTime)
- Retry with exponential backoff (3 attempts; 429/5xx retryable)
- Symbol-level failure isolation (one bad symbol does not abort the batch)
- Rate limiting (Binance weight-based; ~2 req/s budget)

## 7. Validation Pipeline (ADR-003)

Every row passes `validate_raw_observation()` before persisting. Invalid rows are dropped and counted; if invalid ratio > 1%, the symbol batch fails (fails loud).

## 8. Registration

After artifact write: `DatasetRegistry.register(Dataset(...))`. The engine stops there — no further processing.

## 9. Acceptance Criteria

- klines / funding / oi downloadable with retry, backoff, pagination
- every observation validated
- every dataset has manifest + content_hash + dataset_id
- `check_dataset_id()` re-verifiable
- dataset registered in DatasetRegistry
- immutable: writing to an existing dataset_id is an error

## 10. Testing

- downloader tests (pagination, retry/backoff, failure isolation) with mocked HTTP
- validation tests (reuse test_validation.py)
- manifest + dataset_id tests
- registry integration test (register → get → immutable)
