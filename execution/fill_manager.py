from dataclasses import dataclass

from models.book import MarketBook
from models.enums import Side


@dataclass(slots=True)
class FillResult:
    filled: bool
    fill_price: float | None
    fill_size: float
    reason: str


def simulate_entry_fill(
    book: MarketBook,
    side: Side,
    limit_price: float,
    size: float,
    model: str = "conservative",
) -> FillResult:
    side_book = book.yes if side == Side.YES else book.no
    if side_book.best_ask is None:
        return FillResult(False, None, 0.0, "missing_best_ask")
    if side_book.best_ask.price > limit_price:
        return FillResult(False, None, 0.0, "ask_above_limit")
    if side_book.best_ask.size < size:
        return FillResult(False, None, side_book.best_ask.size, "partial_depth_only")
    if model == "midpoint_touch" and side_book.midpoint is not None:
        return FillResult(True, side_book.midpoint, size, "filled_midpoint_touch")
    return FillResult(True, side_book.best_ask.price, size, "filled_conservative")


def simulate_exit_fill(book: MarketBook, side: Side, limit_price: float, size: float) -> FillResult:
    side_book = book.yes if side == Side.YES else book.no
    if side_book.best_bid is None:
        return FillResult(False, None, 0.0, "missing_best_bid")
    if side_book.best_bid.price < limit_price:
        return FillResult(False, None, 0.0, "bid_below_limit")
    fill_size = min(size, side_book.best_bid.size)
    if fill_size <= 0:
        return FillResult(False, None, 0.0, "no_bid_depth")
    return FillResult(True, side_book.best_bid.price, fill_size, "filled_exit")
