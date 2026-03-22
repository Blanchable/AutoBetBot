import random
import time

from models.book import BookLevel, MarketBook, SideBook
from models.market import Market


class ClobMarketData:
    """Polling stub. Replace with websocket/polling against Polymarket CLOB in live mode."""

    def get_book(self, market: Market) -> MarketBook:
        base = random.uniform(0.84, 0.92)
        spread = random.uniform(0.005, 0.02)
        yes_bid = round(base - spread / 2, 4)
        yes_ask = round(base + spread / 2, 4)
        no_mid = round(1 - base, 4)
        no_bid = max(0.01, round(no_mid - spread / 2, 4))
        no_ask = min(0.99, round(no_mid + spread / 2, 4))
        return MarketBook(
            market_id=market.market_id,
            yes=SideBook(best_bid=BookLevel(yes_bid, random.uniform(100, 500)), best_ask=BookLevel(yes_ask, random.uniform(100, 500))),
            no=SideBook(best_bid=BookLevel(no_bid, random.uniform(100, 500)), best_ask=BookLevel(no_ask, random.uniform(100, 500))),
            ts_epoch_ms=int(time.time() * 1000),
        )
