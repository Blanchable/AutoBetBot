from dataclasses import dataclass, field
from datetime import datetime

from models.position import Position


@dataclass(slots=True)
class PortfolioState:
    bankroll: float
    open_positions: dict[str, Position] = field(default_factory=dict)
    closed_positions: list[Position] = field(default_factory=list)
    last_exit_by_market: dict[str, datetime] = field(default_factory=dict)

    @property
    def deployed_capital(self) -> float:
        return sum(p.notional for p in self.open_positions.values())

    @property
    def realized_pnl(self) -> float:
        return sum(p.realized_pnl for p in self.closed_positions)

    def exposure_by_asset(self) -> dict[str, float]:
        out: dict[str, float] = {}
        for p in self.open_positions.values():
            out[p.asset.value] = out.get(p.asset.value, 0.0) + p.notional
        return out
