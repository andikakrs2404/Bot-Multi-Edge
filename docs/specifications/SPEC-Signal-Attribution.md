# SPEC-Signal-Attribution

**Status:** DRAFT  
**Date:** 2026-07-27  
**Owner:** Lead Architect  

---

## Purpose

Setiap trade (atau aggregated signal) harus bisa ditelusuri ke semua lapisan yang menghasilkannya. Tanpa ini, PnL analysis cuma bisa bilang "edge E001 profit 10%" — padahal mungkin profit itu berasal dari special situation SS002 yang membuat E001 punya konteks lebih baik.

## Attribution Chain

Setiap signal wajib membawa attribusi penuh:

```
Input Sources (alpha)
    ↓
Situation (opportunity)
    ↓
Edge (signal)
    ↓
Aggregated Signal
    ↓
Trade
```

## Signal Output Schema

```json
{
  "signal_id": "sig-20260727-120100-TAOUSDT",
  "symbol": "TAOUSDT",
  "exchange": "BINANCE",
  "direction": "LONG",
  "aggregated_score": 81,
  "aggregated_confidence": 0.74,
  "source": "focus_queue",
  "source_tier": "A",
  "contributing_edges": [
    { "edge_id": "E001", "score": 87, "confidence": 0.82, "direction": "LONG" },
    { "edge_id": "E003", "score": 72, "confidence": 0.65, "direction": "LONG" }
  ],
  "features_used": {
    "F002": { "raw": 3.42, "pctl_30d": 95 },
    "F003": { "raw": 2.1, "pctl_30d": 88 },
    "F004": { "raw": 1.03, "pctl_30d": 91 }
  },
  "situation": null,
  "breadth_context": {
    "sector": "AI",
    "sector_bull_breadth": 82,
    "breadth_regime": "EXPANSION"
  },
  "attention_context": {
    "attention_score": 86,
    "heat_score": 92
  },
  "alpha_sources": ["A001", "A002", "A003", "A008"],
  "evaluated_at": "2026-07-27T12:01:00.000Z"
}
```

## Field Definitions

| Field | Description |
|-------|-------------|
| `source` | focus_queue or opportunity |
| `source_tier` | A/B/C/D or null (for opportunity) |
| `contributing_edges` | EdgeResults yang masuk aggregator |
| `features_used` | Feature snapshot — values yang dipakai edge |
| `situation` | SS001-SS009 jika signal berasal dari Opportunity Queue |
| `breadth_context` | Sector breadth + regime saat signal |
| `attention_context` | Attention score + heat score saat signal |
| `alpha_sources` | Alpha source ID yang berkontribusi (dari ALPHA-SOURCES.md) |

## Alpha Source Resolution

Dari `features_used` + `situation`, resolve ke alpha source:

```python
def resolve_alpha_sources(signal) -> list[str]:
    sources = set()
    for feature_id in signal.features_used:
        sources.update(ALPHA_SOURCE_BY_FEATURE.get(feature_id, []))
    if signal.situation:
        sources.update(ALPHA_SOURCE_BY_SITUATION.get(signal.situation, []))
    return list(sources)
```

Contoh: signal yang pakai F002, F003, F004 dan berasal dari SS002 → alpha sources = [A001, A002, A003, A005] (OI Expansion, Volume Expansion, Relative Strength, New Listing).

## PnL Analysis Queries

Dengan attribusi ini, bisa jawab:

```sql
-- Profit by alpha source
SELECT alpha_source, SUM(pnl) FROM trades
GROUP BY alpha_source
ORDER BY SUM(pnl) DESC;

-- Profit by situation
SELECT situation_id, COUNT(*), AVG(pnl) FROM trades
WHERE situation_id IS NOT NULL
GROUP BY situation_id;

-- Edges that perform best in EXPANSION regime
SELECT edge_id, AVG(pnl), breadth_regime FROM trades
GROUP BY edge_id, breadth_regime;

-- Alpha source decay over time
SELECT alpha_source, month, AVG(pnl) FROM trades
GROUP BY alpha_source, month
ORDER BY alpha_source, month;
```

## Storage

Signal attribusi disimpan sebagai satu dokumen JSON per signal. Append-only log. Bisa di-query pakai script Python atau SQLite setelah export.

```yaml
signal_store:
  format: jsonl
  path: data/signals/
  retention_days: 365
  indexed_by: [symbol, edge_id, situation_id, timestamp]
```

## Non-Goals (V1)

- Real-time PnL attribution dashboard
- ML-based alpha source contribution estimation
- Automated alpha source ranking

## References

- ALPHA-SOURCES.md
- MARKET-HYPOTHESES.md
- ADR-010: Edge Framework
- ADR-011: Opportunity Pipeline
