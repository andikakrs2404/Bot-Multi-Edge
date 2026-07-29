"""Query wrapper around SymbolRegistry."""

from __future__ import annotations

from typing import Any

from src.market_data.registry import SymbolMeta, SymbolRegistry  # noqa: TID252


class RegistryView:
    """Lightweight query facade over SymbolRegistry.

    No-op when no registry is attached (safe for standalone dev).
    """

    def __init__(self, registry: SymbolRegistry | None = None) -> None:
        self._registry = registry

    def have_registry(self) -> bool:
        return self._registry is not None

    @property
    def count(self) -> int:
        return self._registry.count if self._registry else 0

    def list_active(self, exchange: str | None = None) -> list[SymbolMeta]:
        if self._registry is None:
            return []
        return self._registry.list_active(exchange=exchange)

    def get(self, exchange: str, symbol: str) -> SymbolMeta | None:
        if self._registry is None:
            return None
        return self._registry.get(exchange=exchange, symbol=symbol)
