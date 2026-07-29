# AGENT GUIDELINES

## Sebelum Coding

1. Baca `docs/project/PROJECT-ROADMAP.md` — tentuin fase aktif.
2. Cek `docs/project/TECH-DEBT.md` — fix HIGH debt dulu.
3. Cek `docs/project/DECISION-LOG.md` — hindari keputusan ulang.
4. Buka ADR fase bersangkutan (contoh: Phase 1 = ADR-002).
5. Baru mulai implementasi.

## Ponytail Ladder (DietrichGebert/ponytail)

Before writing any code, stop at the first rung that holds:

1. **Does this need to exist?** (YAGNI) → no: skip. Don't build what nobody asked for.
2. **Already in this codebase?** → reuse it. Cek FEATURE-Registry, EDGE-Registry, SPEC-Special-Situations, existing modules.
3. **Stdlib does it?** → use it. No new dependency.
4. **Native platform feature?** → use it (CSS over JS, `<input type=date>` over datepicker).
5. **Already-installed dependency?** → use it. Never add a new dep for what a few lines can do.
6. **Can this be one line?** → one line.
7. **Only then: minimum code that works.**

### Domain-Specific Extensions

| Sebelum... | WAJIB cek |
|-----------|-----------|
| New Feature | FEATURE-Registry.md — existing? bisa di-extension? overlap? |
| New Edge | EDGE-Registry.md — existing? bisa dimodifikasi? overlap sinyal? |
| New Detector | SPEC-Special-Situations.md — existing? trigger bisa ditambah ke situation existing? |
| New ADR | Semua ADR + DECISION-LOG.md — sudah dicakup? cukup decision log? |
| Any code | Stdlib, dep existing, OSS reference pattern |

### Forbidden

```yaml
forbidden:
  - duplicate_feature:   F sama fungsinya dengan F existing
  - duplicate_edge:      E sama sinyalnya dengan E existing
  - duplicate_detector:  SS sama trigger-nya dengan SS existing
  - duplicate_adr:       Masalah sama dibahas ADR beda
  - new_dependency:      Kalau bisa stdlib / dep existing
```

### ponytail: Marker

Setiap deliberate simplification (global lock, O(n²) scan, naive heuristic) yang potensi jadi masalah di masa depan harus ditandai dengan komentar `ponytail:` yang menyebut ceiling dan upgrade path:

```python
# ponytail: O(n²) scan on symbol list, ok for <5K symbols.
# Replace with hash lookup if universe grows past 10K.
```

### Test Rule

Non-trivial logic leaves ONE runnable check — assert-based self-check or one small test file. No frameworks, no fixtures. Trivial one-liners need no test.

## Pipeline Rules

- Feature Store = raw only. Normalisasi di layer terpisah.
- Attention score alone tidak boleh exclude symbol. Opportunity Pipeline bypass.
- Dua entry path ke Edge Engine: Focus Queue (Tier A/B) dan Opportunity Queue.
- Setiap trade harus traceable ke edge + situation + features.
- Error isolation per edge. Satu mati, yang lain jalan.

## Tech Debt Rule

Setiap shortcut HARUS dicatat di TECH-DEBT.md. Format:
```
TD-NNN: Deskripsi, Fase, Dampak (LOW/MED/HIGH), Rencana fix
```

## Graphify Knowledge Graph

Graphify diinstall dengan `graphify hermes install`. File knowledge graph di `graphify-out/graph.json`.

Sebelum menjawab pertanyaan tentang relasi antar komponen arsitektur (feature → edge → ADR → situation), baca `graphify-out/graph.json` dulu untuk navigasi cepat. Gunakan `graphify path "NodeA" "NodeB" --graph graphify-out/graph.json` untuk shortest path antar node.

### Graph Node Types

| Type | Examples |
|------|----------|
| ADR | ADR-001 s/d ADR-011 |
| SPEC | SPEC-Symbol-State, SPEC-Special-Situations |
| Registry | FEATURE-Registry, EDGE-Registry |
| Certification | FEATURE-Certification, EDGE-Certification |
| Research | MARKET-Hypotheses, ALPHA-Sources, RESEARCH-Backlog |
| Project | PROJECT-Roadmap, TECH-DEBT, DECISION-LOG, SYSTEM-Constraints |
| Reference | GITHUB-References, REFERENCES |

### Common Queries

- "Apa dependensi ADR-005?" → cek edges dengan source=ADR-005
- "Feature apa yang dipakai E001?" → FEATURE-Registry → EDGE-Registry
- "Dari hypothesis mana edge ini berasal?" → MARKET-Hypotheses → EDGE-Registry
- "Situation apa yang bypass attention?" → SPEC-Special-Situations → ADR-011
- "Siapa yang butuh Alpha Source OI Expansion?" → ALPHA-Sources → FEATURE-Registry, EDGE-Registry
