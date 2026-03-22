from dataclasses import dataclass

from app.config import Settings
from models.book import MarketBook
from models.enums import ExitReason
from models.position import Position


@dataclass(slots=True)
class ExitCheck:
    should_exit: bool
    reason: ExitReason | None
    limit_price: float | None


def check_exit(settings: Settings, position: Position, book: MarketBook, seconds_left: int) -> ExitCheck:
    side_book = book.yes if position.side.value == "YES" else book.no
    if side_book.best_bid is None:
        return ExitCheck(False, None, None)

    bid = side_book.best_bid.price
    if bid >= settings.tp_price:
        return ExitCheck(True, ExitReason.TAKE_PROFIT, settings.tp_price)
    if bid <= settings.sl_price:
        return ExitCheck(True, ExitReason.STOP_LOSS, bid)
    if seconds_left <= settings.time_stop_seconds:
        return ExitCheck(True, ExitReason.TIME_STOP, bid)
    return ExitCheck(False, None, None)
