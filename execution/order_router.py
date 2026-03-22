from dataclasses import dataclass
from datetime import datetime, timedelta
import uuid

from app.config import Settings
from execution.fill_manager import FillResult, simulate_entry_fill, simulate_exit_fill
from models.book import MarketBook
from models.enums import Side


@dataclass(slots=True)
class OrderRequest:
    market_id: str
    side: Side
    size: float
    limit_price: float
    is_entry: bool


@dataclass(slots=True)
class OrderOutcome:
    order_id: str
    status: str
    fill: FillResult


class OrderRouter:
    def __init__(self, settings: Settings):
        self.settings = settings

    def submit_paper(self, req: OrderRequest, book: MarketBook, now: datetime, created_at: datetime) -> OrderOutcome:
        timeout = self.settings.entry_order_timeout_sec if req.is_entry else self.settings.exit_order_timeout_sec
        if now - created_at > timedelta(seconds=timeout):
            return OrderOutcome(str(uuid.uuid4()), "cancelled_timeout", FillResult(False, None, 0.0, "timeout"))

        fill = (
            simulate_entry_fill(book, req.side, req.limit_price, req.size, self.settings.paper_fill_model)
            if req.is_entry
            else simulate_exit_fill(book, req.side, req.limit_price, req.size)
        )
        status = "filled" if fill.filled else "rejected"
        return OrderOutcome(str(uuid.uuid4()), status, fill)
