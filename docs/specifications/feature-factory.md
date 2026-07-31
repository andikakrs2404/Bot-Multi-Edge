# Specification: Feature Factory

Derived from: ADR-000B (Trust Model), ADR-002 (Domain Ontology), ADR-005 (Registry Model), ADR-003 (Data Contract)
Constitution: be37bf97... (Freeze v1.0, 2026-07-29)

Status: Draft (v0.1)

## 1. Trust Level

Feature Factory produces **Trust Level 2** artifacts (FeatureSnapshot):

```text
Dataset (L1) + registered FeatureIDs (L2 definition)
    → FeatureSnapshot parquet
    → manifest.json → snapshot_id → register
```

It NEVER produces Rule, Edge, or Evidence (those belong to Experiment layer, L3+).

## 2. Inputs

| Input | Source | Constraint |
| --- | --- | --- |
| Dataset | DatasetRegistry (klines, 30m) | must be REGISTERED |
| Feature definitions | FeatureRegistry | each FeatureID MUST be registered ACTIVE |
| Label definitions | LabelRegistry | optional; research datasets only |

Unregistered FeatureID → hard error (ADR-005: identity from registry, not code).

## 3. Outputs

```text
data/features/<snapshot_id>/
    snapshot.parquet       # one row per (symbol, ts)
    manifest.json
```

snapshot.parquet columns (ADR-003 FeatureSnapshot contract):

```text
ts, symbol, exchange, tier,
<feature_id>...           # one column per registered FeatureID
label_<label_id>...       # research datasets only
```

## 4. Feature Computation

All features are computed **per symbol** from raw OHLCV (no cross-sectional
leakage). Deterministic: same dataset + same feature version → same output.

| FeatureID | Definition | Params |
| --- | --- | --- |
| `RSI_14_CLOSE` | RSI(14) on close | 14 |
| `EMA_20_SLOPE` | slope of EMA(20), normalized by close | 20 |
| `ATR_14_PCT` | ATR(14) / close | 14 |
| `VOL_Z_20` | z-score of volume vs rolling 20 | 20 |
| `RET_1H` | 2-bar (30m) log return | — |
| `CANDLE_BODY` | (close-open)/high-low | — |
| `CANDLE_UPPER_WICK` | (high-max(o,c))/high-low | — |
| `CANDLE_LOWER_WICK` | (min(o,c)-low)/high-low | — |
| `RANGE_EXPANSION` | (high-low)/EMA20(high-low) | 20 |
| `OIPCT_1H` | OI 1h change % (from OI dataset) | — |
| `FUNDING_Z_20` | z-score of funding rate vs rolling 20 | 20 |

## 5. Labels (research datasets only)

| LabelID | Definition |
| --- | --- |
| `FWD_RET_24H` | close[t+48] / close[t] - 1 (30m bars, 24h horizon) |
| `TIME_TO_TP_SL` | (bars to first TP/SL hit, TP/SL flags) |
| `FIRST_EVENT` | enum: tp_hit \| sl_hit \| none within horizon |
| `HIT_TARGET` | bool: TP hit before SL within horizon |

Labels are forward-looking by definition — **never** present in production
snapshots (ADR-002 realm separation).

## 6. Snapshot Manifest

```yaml
snapshot_id:      # SHA256(manifest body)
dataset_id:       # source dataset
feature_ids: [...]
label_ids: [...]  # optional
universe_id:
tier_map: {symbol: tier}
row_count:
content_hash:
constitution_hash:
created_at:       # excluded from hash (provenance)
```

## 7. Registration

Snapshot registered in DatasetRegistry as `dataset_type: feature_snapshot`
with `parent_ids = (source dataset_id,)` (ADR-004 lineage). Engine stops here.

## 8. Acceptance Criteria

- unregistered FeatureID rejected
- features computed per symbol, deterministic
- snapshot has manifest + content_hash + snapshot_id
- lineage parent_ids recorded
- registered in DatasetRegistry
- labels only in research snapshots (flag)

## 9. Testing

- feature math correctness (hand-computed cases, RSI/ATR/EMA)
- unregistered feature rejection
- snapshot manifest + id + lineage
- registry integration
- trust boundary: factory code contains no Rule/Edge/Evidence construction
