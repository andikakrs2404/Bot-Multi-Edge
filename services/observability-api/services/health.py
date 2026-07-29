"""Health score computation from ObservabilityStore."""

from __future__ import annotations

from store import ObservabilityStore  # noqa: TID252


async def compute_health_score(store: ObservabilityStore) -> float:
    """Overall system health, averaged across exchanges.

    Per exchange: if connected, 100 - (reconnects * 5), capped 0-100.
    If disconnected, 0.  Returns 100.0 when no data exists.
    """
    connections = await store.get_all_connections()
    if not connections:
        return 100.0

    scores: list[float] = []
    for exchange in connections:
        latest = await store.latest_status(exchange)
        is_connected = getattr(latest, "is_connected", False) if latest else False
        if not is_connected:
            scores.append(0.0)
        else:
            reconnects = await store.reconnect_count(exchange)
            scores.append(max(0.0, min(100.0, 100.0 - reconnects * 5)))

    return sum(scores) / len(scores)
