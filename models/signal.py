from dataclasses import dataclass, field
from datetime import datetime, timezone

from models.enums import Asset, Horizon, Side


@dataclass(slots=True)
class CandidateSignal:
    asset: Asset
    horizon: Horizon
    market_id: str
    favorite_side: Side
    favorite_midpoint: float
    best_bid: float
    best_ask: float
    spread: float
    best_ask_depth: float
    seconds_to_expiry: int
    entry_reason: str
    ranking_score: float = 0.0
    rejection_reason: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
