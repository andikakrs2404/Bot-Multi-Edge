"""System status & WebSocket router."""
from __future__ import annotations

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect

from models import ExchangeStatus, SystemStatusResponse  # noqa: TID252
from services.health import compute_health_score  # noqa: TID252
from services.registry_view import RegistryView  # noqa: TID252
from store import ObservabilityStore  # noqa: TID252

router = APIRouter()


@router.get("/api/system/status", response_model=SystemStatusResponse)
async def system_status(request: Request):
    store: ObservabilityStore = request.app.state.store
    connections = await store.get_all_connections()
    health = await compute_health_score(store)
    reg: RegistryView = request.app.state.registry_view

    exchanges = []
    for exchange, events in connections.items():
        latest = events[-1] if events else None
        is_connected = getattr(latest, "is_connected", False) if latest else False
        uptime = 0.0  # ponytail: track uptime per exchange in V2
        reconnects = await store.reconnect_count(exchange)
        exchanges.append(
            ExchangeStatus(
                exchange=exchange,
                is_connected=is_connected,
                uptime_seconds=uptime,
                reconnect_count=reconnects,
            )
        )

    return SystemStatusResponse(
        exchanges=exchanges,
        health_score=health,
        total_symbols=reg.count if reg.have_registry() else 0,
    )


@router.websocket("/ws/status")
async def ws_status(websocket: WebSocket):
    await websocket.accept()
    store: ObservabilityStore = websocket.app.state.store
    try:
        while True:
            await websocket.receive_text()
            connections = await store.get_all_connections()
            payload: dict[str, dict] = {}
            for exchange, events in connections.items():
                if events:
                    latest = events[-1]
                    payload[exchange] = {
                        "is_connected": getattr(latest, "is_connected", False),
                        "reason": getattr(latest, "reason", None),
                    }
            await websocket.send_json(payload)
    except WebSocketDisconnect:
        pass
