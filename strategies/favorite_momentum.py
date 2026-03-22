from dataclasses import dataclass

from app.config import Settings
from models.book import MarketBook
from models.market import Market
from models.signal import CandidateSignal


@dataclass(slots=True)
class StrategyDecision:
    candidate: CandidateSignal | None
    reason: str


def _in_time_window(settings: Settings, market: Market, seconds_left: int) -> bool:
    if market.horizon.value == "5m":
        return settings.min_seconds_left_5m <= seconds_left <= settings.max_seconds_left_5m
    return settings.min_seconds_left_15m <= seconds_left <= settings.max_seconds_left_15m


def evaluate_market(
    settings: Settings,
    market: Market,
    book: MarketBook,
    seconds_left: int,
    min_required_depth: float,
) -> StrategyDecision:
    fav = book.favorite_side()
    if fav is None:
        return StrategyDecision(None, "missing_book")

    side, side_book = fav
    if side_book.best_ask is None or side_book.best_bid is None:
        return StrategyDecision(None, "missing_quotes")

    mid = side_book.midpoint
    spread = side_book.spread
    if mid is None or spread is None:
        return StrategyDecision(None, "missing_mid_spread")

    if mid < settings.entry_mid_min:
        return StrategyDecision(None, "mid_below_threshold")
    if side_book.best_ask.price > settings.entry_ask_max:
        return StrategyDecision(None, "ask_above_threshold")
    if spread > settings.max_spread:
        return StrategyDecision(None, "spread_too_wide")
    if not _in_time_window(settings, market, seconds_left):
        return StrategyDecision(None, "outside_time_window")
    if side_book.best_ask.size < min_required_depth:
        return StrategyDecision(None, "insufficient_depth")

    signal = CandidateSignal(
        asset=market.asset,
        horizon=market.horizon,
        market_id=market.market_id,
        favorite_side=side,
        favorite_midpoint=mid,
        best_bid=side_book.best_bid.price,
        best_ask=side_book.best_ask.price,
        spread=spread,
        best_ask_depth=side_book.best_ask.size,
        seconds_to_expiry=seconds_left,
        entry_reason="favorite_momentum_filters_passed",
    )
    return StrategyDecision(signal, "eligible")


def rank_signal(signal: CandidateSignal, concentration_penalty: float = 0.0) -> float:
    spread_score = max(0.0, (0.03 - signal.spread) * 30)
    favorite_score = signal.favorite_midpoint * 3
    time_score = min(1.0, signal.seconds_to_expiry / 720) * 2
    depth_score = min(2.0, signal.best_ask_depth / 400)
    score = spread_score + favorite_score + time_score + depth_score - concentration_penalty
    signal.ranking_score = round(score, 4)
    return signal.ranking_score
