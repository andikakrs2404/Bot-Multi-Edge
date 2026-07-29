"""Observability API — FastAPI app with CORS.

Wires up pipeline EventBus, SymbolRegistry, and ObservabilityStore
in lifespan so dashboard can display live data.

Run:  python -m api          (from services/observability-api/)
      uvicorn api:app        (from services/observability-api/)
"""

from __future__ import annotations

import asyncio
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# hyphenated dir can't be a Python package — add service & project root to sys.path
_SVC_DIR = str(Path(__file__).parent.resolve())
_PROJ_DIR = str(Path(__file__).resolve().parents[2])
sys.path.insert(0, _SVC_DIR)
if _PROJ_DIR not in sys.path:
    sys.path.append(_PROJ_DIR)

from routers import symbols, system  # noqa: E402
from services.registry_view import RegistryView  # noqa: E402
from src.market_data.event_bus import EventBus  # noqa: E402
from src.market_data.events import ConnectionStatus, Event  # noqa: E402
from src.market_data.registry import SymbolRegistry  # noqa: E402
from store import ObservabilityStore  # noqa: E402


@asynccontextmanager
async def _lifespan(app: FastAPI):
    # ── Shared pipeline bus ──
    pipeline_bus = EventBus()
    store = ObservabilityStore()

    # ── Registry polls REST, publishes SymbolEvent on pipeline_bus ──
    registry = SymbolRegistry(event_bus=pipeline_bus)
    registry_task = asyncio.create_task(registry.start())

    # ── Store subscribes to pipeline bus for ConnectionStatus ──
    async def _connection_handler(ev: Event) -> None:
        if isinstance(ev, ConnectionStatus):
            exchange = ev.exchange.value if hasattr(ev.exchange, "value") else str(ev.exchange)
            await store.update_from_connection_status(exchange, ev)

    pipeline_bus.subscribe(_connection_handler, events={ConnectionStatus})

    # ── Start delivery loop ──
    await pipeline_bus.start()

    # ── Expose to route handlers ──
    app.state.store = store
    app.state.registry_view = RegistryView(registry)
    app.state.pipeline_bus = pipeline_bus

    yield

    # ── Shutdown ──
    registry_task.cancel()
    try:
        await registry_task
    except asyncio.CancelledError:
        pass
    await pipeline_bus.stop()


app = FastAPI(title="Observability API", version="0.1.0", lifespan=_lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(system.router)
app.include_router(symbols.router)
