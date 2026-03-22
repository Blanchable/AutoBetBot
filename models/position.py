from dataclasses import dataclass, field
from datetime import datetime, timezone

from models.enums import Asset, ExitReason, Horizon, PositionStatus, Side


@dataclass(slots=True)
class Position:
    position_id: str
    market_id: str
    asset: Asset
    horizon: Horizon
    side: Side
    entry_price: float
    entry_size: float
    target_price: float
    stop_price: float
    time_stop_threshold: int
    status: PositionStatus = PositionStatus.OPEN
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    entry_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    exit_time: datetime | None = None
    exit_reason: ExitReason | None = None

    @property
    def notional(self) -> float:
        return self.entry_price * self.entry_size
