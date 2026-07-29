# TECH-DEBT

Semua shortcut, temporary fix, dan keputusan suboptimal yang diambil selama implementasi. Wajib dicatat biar gak hilang.

Format:

```
TD-NNN
Deskripsi: ...
Dibuat: YYYY-MM-DD
Fase: N
Dampak: LOW / MEDIUM / HIGH
Rencana fix: ...
```

## Active

*Belum ada — implementasi belum dimulai.*

## Resolved

*Belum ada.*

## Cara Pakai

1. Tiap kali ambil shortcut (hardcode, skip error handling, tunda optimasi), catat sebagai TD.
2. Tiap awal fase baru, scan TD yang relevan — fix yang HIGH dulu.
3. Kalau TD gak relevan lagi, pindah ke Resolved dengan catatan.
