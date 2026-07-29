"""Pydantic response models for observability API."""

from __future__ import annotations

from pydantic import BaseModel


class ExchangeStatus(BaseModel):
    exchange: str
    is_connected: bool
    uptime_seconds: float
    reconnect_count: int


class SystemStatusResponse(BaseModel):
    exchanges: list[ExchangeStatus]
    health_score: float
    total_symbols: int = 0


class SymbolResponse(BaseModel):
    symbol: str
    exchange: str
    sector: str
    tags: list[str]
    listing_age_days: int
    status: str


class SymbolListResponse(BaseModel):
    total: int
    per_exchange: dict[str, int]
    per_sector: dict[str, int]
    symbols: list[SymbolResponse]
    classification_coverage: float = 0.0  # 0-1, classified / total
