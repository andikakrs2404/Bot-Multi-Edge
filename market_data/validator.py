"""Sequence Validator — detect gaps, duplicates, out-of-order per symbol.

Uses Exchange enum for type-safe exchange identification.
"""

from __future__ import annotations

from collections import defaultdict

from .events import Exchange


class SequenceValidator:
    """Per-exchange, per-symbol sequence tracking.

    Detects:
    - Missing sequence (gap)
    - Duplicate sequence
    - Out-of-order (< last seen)

    Reorder buffer: max N slots for out-of-order, drop if exceeded.
    """

    def __init__(self, reorder_buffer: int = 5) -> None:
        self._last_seq: dict[str, int] = defaultdict(int)
        self._gap_count: dict[str, int] = defaultdict(int)
        self._reorder: dict[str, list[int]] = defaultdict(list)
        self._reorder_buffer = reorder_buffer

    def validate(self, exchange: Exchange | str, symbol: str, seq: int) -> str | None:
        """Check sequence anomaly. Returns anomaly type or None."""
        key = f"{exchange}:{symbol}"

        if seq == self._last_seq[key]:
            return "duplicate"
        if seq < self._last_seq[key]:
            if len(self._reorder[key]) < self._reorder_buffer:
                self._reorder[key].append(seq)
                return "out_of_order_buffered"
            return "out_of_order_dropped"
        if self._last_seq[key] > 0 and seq > self._last_seq[key] + 1:
            self._gap_count[key] += 1
            self._last_seq[key] = seq
            return "gap"
        self._last_seq[key] = seq
        return None

    def reset(
        self,
        symbol: str | None = None,
        exchange: Exchange | str | None = None,
    ) -> None:
        if exchange and symbol:
            key = f"{exchange}:{symbol}"
            self._last_seq[key] = 0
            self._gap_count[key] = 0
            self._reorder[key].clear()
        else:
            self._last_seq.clear()
            self._gap_count.clear()
            self._reorder.clear()

    @property
    def total_gaps(self) -> int:
        return sum(self._gap_count.values())
