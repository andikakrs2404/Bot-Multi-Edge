# ALPHA-SOURCES

Semua sumber alpha dalam sistem. Setiap feature dan situation adalah alpha source. Tracking siapa yang menggunakan, dan nanti PnL kontribusi.

## Sumber Alpha

| ID | Name | Used By Edges | Used By Situations | PnL Contribution |
|----|------|---------------|-------------------|-------------------|
| A001 | OI Expansion | E001, E004 | SS002 | unknown |
| A002 | Volume Expansion | E001, E003, E004 | — | unknown |
| A003 | Relative Strength | E001, E003, E005 | — | unknown |
| A004 | Compression | E004 | — | unknown |
| A005 | Funding Rate | E002 | SS004 | unknown |
| A006 | Liquidation Cascade | — | SS003 | unknown |
| A007 | New Listing | — | SS001 | unknown |
| A008 | Sector Breadth | E001, E003, E007 | SS006 | unknown |
| A009 | Leader Movement | E005 | — | unknown |
| A010 | Volume Anomaly | — | SS007 | unknown |

## Detail

### A001 — OI Expansion

```yaml
id: A001
name: OI Expansion
feature: F002
situation: SS002

used_by:
  edges: [E001, E004]
  situations: [SS002]

category: liquidity
pipeline_stage: feature_store

pnl_contribution: unknown
notes: Alpha source paling kuat sejauh ini (E001 confidence 91).
```

### A002 — Volume Expansion

```yaml
id: A002
name: Volume Expansion
feature: F003

used_by:
  edges: [E001, E003, E004]
  situations: []

category: momentum
pipeline_stage: feature_store

pnl_contribution: unknown
notes: Digunakan oleh 3 edges. Paling banyak dikonsumsi.
```

### A008 — Sector Breadth

```yaml
id: A008
name: Sector Breadth
feature: null (breadth engine)

used_by:
  edges: [E001, E003]
  situations: [SS006]

category: context
pipeline_stage: breadth

pnl_contribution: unknown
notes: Bukan feature — output dari ADR-006. Memberi konteks sektor.
```

## Cara Pakai

1. Setiap feature baru → daftar sebagai alpha source.
2. Setiap situation baru → daftar sebagai alpha source.
3. Setelah PnL tracking jalan → isi `pnl_contribution` otomatis.
4. Ranking alpha source per kuantil performa.
