from dataclasses import dataclass
from datetime import datetime, timedelta

from app.config import Settings
from models.signal import CandidateSignal
from models.portfolio import PortfolioState
from risk.exposure import deployed_fraction


@dataclass(slots=True)
class LimitDecision:
    approved: bool
    reason: str


def check_limits(
    settings: Settings,
    portfolio: PortfolioState,
    signal: CandidateSignal,
    estimated_notional: float,
    now: datetime,
) -> LimitDecision:
    if signal.market_id in portfolio.open_positions:
        return LimitDecision(False, "position_already_open")

    if len(portfolio.open_positions) >= settings.max_open_positions_global:
        return LimitDecision(False, "max_open_positions_global")

    per_asset = sum(1 for p in portfolio.open_positions.values() if p.asset == signal.asset)
    if per_asset >= settings.max_open_positions_per_asset:
        return LimitDecision(False, "max_open_positions_per_asset")

    per_horizon = sum(1 for p in portfolio.open_positions.values() if p.horizon == signal.horizon)
    if per_horizon >= settings.max_open_positions_per_horizon:
        return LimitDecision(False, "max_open_positions_per_horizon")

    projected = portfolio.deployed_capital + estimated_notional
    if portfolio.bankroll <= 0:
        return LimitDecision(False, "insufficient_bankroll")
    if projected / portfolio.bankroll > settings.max_capital_deployed_fraction:
        return LimitDecision(False, "max_capital_deployed_fraction")

    if estimated_notional > settings.max_position_size_dollars:
        return LimitDecision(False, "max_position_size_dollars")

    if estimated_notional > portfolio.bankroll * settings.max_position_size_fraction:
        return LimitDecision(False, "max_position_size_fraction")

    last_exit = portfolio.last_exit_by_market.get(signal.market_id)
    if last_exit and now - last_exit < timedelta(seconds=settings.cooldown_seconds_after_exit):
        return LimitDecision(False, "cooldown_seconds_after_exit")

    if deployed_fraction(portfolio) >= settings.max_capital_deployed_fraction:
        return LimitDecision(False, "already_fully_deployed")

    return LimitDecision(True, "approved")
