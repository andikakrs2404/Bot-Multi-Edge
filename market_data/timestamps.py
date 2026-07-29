"""Timestamp enrichment helpers — attach exchange_ts, received_ts, processed_ts.

Uses frozen Timestamps dataclass from events.py.
"""

from __future__ import annotations

from datetime import datetime, timezone

from .events import Event, Timestamps


def enrich_timestamps(
    event: Event,
    exchange_ts: datetime | float | None = None,
) -> Event:
    """Set event.timestamps.

    - If event already has timestamps, update exchange_ts only if provided.
    - If not, create fresh Timestamps with received_ts = now.
    - Sets processed_ts = now at the end.
    """
    now = datetime.now(timezone.utc)

    if event.timestamps is None:
        exchange_dt = _ensure_dt(exchange_ts) if exchange_ts is not None else now
        event.timestamps = Timestamps(
            exchange_ts=exchange_dt,
            received_ts=now,
        )
    else:
        if exchange_ts is not None:
            event.timestamps.exchange_ts = _ensure_dt(exchange_ts)
        event.timestamps.received_ts = now

    event.timestamps.processed_ts = now
    return event


def _ensure_dt(val: datetime | float) -> datetime:
    """Normalise float timestamp to UTC datetime."""
    if isinstance(val, datetime):
        return val if val.tzinfo else val.replace(tzinfo=timezone.utc)
    return datetime.fromtimestamp(val, tz=timezone.utc)
