import sqlite3
from datetime import datetime, timezone

from models.book import MarketBook
from models.market import Market
from models.position import Position
from models.signal import CandidateSignal
from storage.schema import DDL


class SQLiteStore:
    def __init__(self, path: str):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        for stmt in DDL:
            self.conn.execute(stmt)
        self.conn.commit()

    def save_market(self, market: Market) -> None:
        self.conn.execute(
            """
            INSERT INTO markets (market_id, asset, horizon, yes_token_id, no_token_id, end_time, is_active, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(market_id) DO UPDATE SET
            asset=excluded.asset, horizon=excluded.horizon, yes_token_id=excluded.yes_token_id,
            no_token_id=excluded.no_token_id, end_time=excluded.end_time, is_active=excluded.is_active,
            updated_at=excluded.updated_at
            """,
            (
                market.market_id,
                market.asset.value,
                market.horizon.value,
                market.yes_token_id,
                market.no_token_id,
                market.end_time.isoformat(),
                1 if market.is_active else 0,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self.conn.commit()

    def save_book_snapshot(self, book: MarketBook) -> None:
        self.conn.execute(
            """INSERT INTO book_snapshots (market_id, ts_epoch_ms, yes_bid, yes_ask, no_bid, no_ask, yes_bid_size, yes_ask_size, no_bid_size, no_ask_size)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                book.market_id,
                book.ts_epoch_ms,
                book.yes.best_bid.price if book.yes.best_bid else None,
                book.yes.best_ask.price if book.yes.best_ask else None,
                book.no.best_bid.price if book.no.best_bid else None,
                book.no.best_ask.price if book.no.best_ask else None,
                book.yes.best_bid.size if book.yes.best_bid else None,
                book.yes.best_ask.size if book.yes.best_ask else None,
                book.no.best_bid.size if book.no.best_bid else None,
                book.no.best_ask.size if book.no.best_ask else None,
            ),
        )
        self.conn.commit()

    def save_signal(self, signal: CandidateSignal, accepted: bool, reason: str) -> None:
        self.conn.execute(
            """INSERT INTO signals (ts, market_id, asset, horizon, side, mid, best_bid, best_ask, spread, seconds_left, score, accepted, reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                signal.created_at.isoformat(),
                signal.market_id,
                signal.asset.value,
                signal.horizon.value,
                signal.favorite_side.value,
                signal.favorite_midpoint,
                signal.best_bid,
                signal.best_ask,
                signal.spread,
                signal.seconds_to_expiry,
                signal.ranking_score,
                1 if accepted else 0,
                reason,
            ),
        )
        self.conn.commit()

    def save_order(self, order_id: str, ts: datetime, market_id: str, is_entry: bool, status: str, reason: str, size: float, limit_price: float, fill_price: float | None, fill_size: float) -> None:
        self.conn.execute(
            """INSERT OR REPLACE INTO orders (order_id, ts, market_id, is_entry, status, reason, size, limit_price, fill_price, fill_size)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (order_id, ts.isoformat(), market_id, 1 if is_entry else 0, status, reason, size, limit_price, fill_price, fill_size),
        )
        self.conn.commit()

    def upsert_position(self, position: Position) -> None:
        self.conn.execute(
            """INSERT OR REPLACE INTO positions (position_id, market_id, asset, horizon, side, entry_price, entry_size, target_price, stop_price, status, realized_pnl, entry_time, exit_time, exit_reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                position.position_id,
                position.market_id,
                position.asset.value,
                position.horizon.value,
                position.side.value,
                position.entry_price,
                position.entry_size,
                position.target_price,
                position.stop_price,
                position.status.value,
                position.realized_pnl,
                position.entry_time.isoformat(),
                position.exit_time.isoformat() if position.exit_time else None,
                position.exit_reason.value if position.exit_reason else None,
            ),
        )
        self.conn.commit()
