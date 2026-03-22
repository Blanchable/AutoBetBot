from dataclasses import dataclass
from datetime import datetime, timezone

from models.enums import Asset, Horizon


@dataclass(slots=True)
class Market:
    market_id: str
    asset: Asset
    horizon: Horizon
    yes_token_id: str
    no_token_id: str
    end_time: datetime
    is_active: bool = True

    def seconds_to_expiry(self, now: datetime | None = None) -> int:
        ref = now or datetime.now(timezone.utc)
        return max(0, int((self.end_time - ref).total_seconds()))
