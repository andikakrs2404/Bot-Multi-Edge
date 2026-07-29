"""Symbol query router."""

from __future__ import annotations

from fastapi import APIRouter, Query, Request, HTTPException

from models import SymbolListResponse, SymbolResponse  # noqa: TID252
from services.registry_view import RegistryView  # noqa: TID252

router = APIRouter()


@router.get("/api/symbols", response_model=SymbolListResponse)
async def list_symbols(request: Request, exchange: str | None = Query(None)):
    view: RegistryView = request.app.state.registry_view
    symbols = view.list_active(exchange=exchange)

    per_exchange: dict[str, int] = {}
    per_sector: dict[str, int] = {}
    responses: list[SymbolResponse] = []

    for s in symbols:
        ex = str(s.exchange)
        per_exchange[ex] = per_exchange.get(ex, 0) + 1
        per_sector[s.sector] = per_sector.get(s.sector, 0) + 1
        responses.append(
            SymbolResponse(
                symbol=s.symbol,
                exchange=ex,
                sector=s.sector,
                tags=list(s.tags),
                listing_age_days=s.listing_age_days,
                status=s.status,
            )
        )

    return SymbolListResponse(
        total=len(responses),
        per_exchange=per_exchange,
        per_sector=per_sector,
        symbols=responses,
        classification_coverage=round(
            (len(responses) - per_sector.get("OTHER", 0)) / len(responses), 3
        ) if responses else 0.0,
    )


@router.get("/api/symbols/{symbol}", response_model=SymbolResponse)
async def get_symbol(
    request: Request, symbol: str, exchange: str = Query("BINANCE")
):
    view: RegistryView = request.app.state.registry_view
    meta = view.get(exchange, symbol)
    if meta is None:
        raise HTTPException(
            status_code=404,
            detail=f"Symbol {exchange}:{symbol} not found",
        )
    return SymbolResponse(
        symbol=meta.symbol,
        exchange=str(meta.exchange),
        sector=meta.sector,
        tags=list(meta.tags),
        listing_age_days=meta.listing_age_days,
        status=meta.status,
    )
