"""AlphaOS runtime artifacts.

Runtime artifacts (MarketSnapshot) are point-in-time observations of live
market state. They are NOT domain objects — they stay out of
`shared/contracts.py` (ADR-002 ontology separation, ADR-003 data contract).
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone

from .contracts import content_hash


@dataclass(frozen=True, slots=True)
class MarketSnapshot:
    snapshot_id: str
    symbol: str
    timestamp: datetime
    feature_values: dict[str, float]

    def __post_init__(self) -> None:
        if not self.feature_values:
            raise ValueError("feature_values must not be empty")
        if self.timestamp.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware (UTC)")
        for name, value in self.feature_values.items():
            if not math.isfinite(value):
                raise ValueError(f"feature {name} must be finite, got {value}")


def make_snapshot_id(symbol: str, timestamp: datetime,
                     feature_values: dict[str, float]) -> str:
    body = json.dumps({
        "symbol": symbol,
        "timestamp": timestamp.isoformat(),
        "feature_values": {k: feature_values[k] for k in sorted(feature_values)},
    }, sort_keys=True)
    return content_hash(body)
