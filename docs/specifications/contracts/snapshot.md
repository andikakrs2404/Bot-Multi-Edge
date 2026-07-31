# Specification: Raw & Snapshot Contracts

Derived from: ADR-003 (Data Contract), ADR-004 (Dataset Versioning)

Status: Draft (v0.1) — must be ratified together with the constitution package.

## Raw Observation Contracts (Trust Level 0)

| Field | Type | Notes |
| --- | --- | --- |
| `ts` | datetime64[ns, UTC] | event time |
| `exchange` | string | e.g. `binance_futures` |
| `symbol` | string | e.g. `BTCUSDT` |
| `open/high/low/close` | float64 | quote currency |
| `volume` | float64 | base currency |
| `quote_volume` | float64 | optional |
| `open_interest` | float64 | optional, OI series |
| `funding_rate` | float64 | optional, funding series |
| `liquidation_side/qty/price` | string/float64/float64 | optional, liq series |

## FeatureSnapshot Contract (Trust Level 2)

One row = one symbol × one timestamp.

| Field | Type | Notes |
| --- | --- | --- |
| `ts` | datetime64[ns, UTC] | snapshot time |
| `symbol` | string | |
| `exchange` | string | |
| `tier` | string | LARGE / MID / SMALL |
| `close` | float64 | |
| `<feature_id>` | float64 | one column per registered FeatureID (ADR-005) |
| `label_<label_id>` | float64 | one column per registered LabelID (research datasets only) |

## Manifest (per Dataset)

```json
{
  "dataset_id": "sha256...",
  "schema_version": "1.0",
  "universe": "top500_perp",
  "timeframe": "30m",
  "date_range": ["2023-01-01", "2026-07-29"],
  "source_version": "...",
  "content_hash": "sha256...",
  "parent_ids": []
}
```

## Validation Rules

- `ts` strictly increasing per (symbol, exchange).
- No NaN in identity columns (`ts`, `symbol`, `exchange`).
- Feature columns present must match the registered FeatureIDs exactly.
