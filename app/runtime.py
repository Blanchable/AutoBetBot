from collections import defaultdict
from datetime import datetime, timezone
import logging
import time
import uuid

from app.config import Settings
from connectors.clob_marketdata import ClobMarketData
from connectors.clob_trading import ClobTrading
from connectors.gamma_client import GammaClient
from dashboard.console_dashboard import render_dashboard
from execution.exit_manager import check_exit
from execution.order_router import OrderRequest, OrderRouter
from models.enums import PositionStatus
from models.portfolio import PortfolioState
from models.position import Position
from risk.portfolio_limits import check_limits
from risk.sizing import size_for_trade
from storage.sqlite_store import SQLiteStore
from strategies.favorite_momentum import evaluate_market, rank_signal
from utils.time_utils import is_stale

LOGGER = logging.getLogger(__name__)


class BotRuntime:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.store = SQLiteStore(settings.sqlite_path)
        self.gamma = GammaClient()
        self.marketdata = ClobMarketData()
        self.live_trading = ClobTrading()
        self.router = OrderRouter(settings)
        self.portfolio = PortfolioState(bankroll=settings.bankroll)
        self.running = False
        self.last_candidate_count = 0
        self.last_discovered_count = 0
        self.last_error: str | None = None
        self.latest_books_by_asset: dict[str, dict[str, float | str]] = {}

    def stop(self) -> None:
        self.running = False

    def snapshot(self) -> dict[str, str | float | int | list[dict[str, float | str]]]:
        return {
            "running": int(self.running),
            "bankroll": self.portfolio.bankroll,
            "deployed": self.portfolio.deployed_capital,
            "open_positions": len(self.portfolio.open_positions),
            "realized_pnl": self.portfolio.realized_pnl,
            "candidate_count": self.last_candidate_count,
            "discovered_count": self.last_discovered_count,
            "last_error": self.last_error or "",
            "books": list(self.latest_books_by_asset.values()),
        }

    def _lane_enabled(self, asset: str, horizon: str) -> bool:
        key = f"enable_{asset.lower()}_{'5m' if horizon == '5m' else '15m'}"
        return bool(getattr(self.settings, key, False))

    def run(self) -> None:
        tracked = {}
        recent_rejections: list[str] = []
        last_discovery = 0.0
        self.running = True
        if self.settings.mode.value == "live":
            LOGGER.warning("MODE=live selected; live execution scaffold is not implemented in v1. Entries are skipped safely.")
        try:
            while self.running:
                now = datetime.now(timezone.utc)
                if time.time() - last_discovery > self.settings.discovery_interval_sec:
                    try:
                        discovered = self.gamma.discover_markets()
                        tracked = {
                            m.market_id: m
                            for m in discovered
                            if m.is_active and self._lane_enabled(m.asset.value, m.horizon.value)
                        }
                        self.last_discovered_count = len(tracked)
                        for m in tracked.values():
                            self.store.save_market(m)
                        last_discovery = time.time()
                        LOGGER.info("discovered_markets=%s", len(tracked))
                    except Exception as exc:  # noqa: BLE001
                        self.last_error = str(exc)
                        LOGGER.exception("market discovery failed; continuing safely: %s", exc)
                        time.sleep(self.settings.poll_interval_ms / 1000)
                        continue

                candidates = []
                concentration = defaultdict(int)
                for p in self.portfolio.open_positions.values():
                    concentration[(p.asset.value, p.horizon.value)] += 1

                for market in tracked.values():
                    secs = market.seconds_to_expiry(now)
                    book = self.marketdata.get_book(market)
                    self.store.save_book_snapshot(book)
                    self.latest_books_by_asset[market.asset.value] = {
                        "asset": market.asset.value,
                        "horizon": market.horizon.value,
                        "yes_bid": round(book.yes.best_bid.price, 4) if book.yes.best_bid else 0.0,
                        "yes_ask": round(book.yes.best_ask.price, 4) if book.yes.best_ask else 0.0,
                        "yes_mid": round(book.yes.midpoint or 0.0, 4),
                        "no_bid": round(book.no.best_bid.price, 4) if book.no.best_bid else 0.0,
                        "no_ask": round(book.no.best_ask.price, 4) if book.no.best_ask else 0.0,
                        "no_mid": round(book.no.midpoint or 0.0, 4),
                    }

                    if is_stale(book.ts_epoch_ms, self.settings.stale_data_ms, now):
                        recent_rejections.append(f"{market.market_id}:stale_data")
                        continue

                    size = size_for_trade(self.settings, self.portfolio.bankroll, market.asset, max(book.yes.best_ask.price, book.no.best_ask.price))
                    decision = evaluate_market(self.settings, market, book, secs, size * self.settings.min_required_depth_multiple)
                    if decision.candidate is None:
                        recent_rejections.append(f"{market.market_id}:{decision.reason}")
                        continue

                    penalty = concentration[(market.asset.value, market.horizon.value)] * 0.8
                    rank_signal(decision.candidate, penalty)
                    candidates.append((decision.candidate, book))

                candidates.sort(key=lambda x: x[0].ranking_score, reverse=True)
                self.last_candidate_count = len(candidates)

                for signal, book in candidates:
                    if self.settings.mode.value == "live":
                        LOGGER.warning("Skipping live entry for market=%s until live execution is implemented", signal.market_id)
                        continue

                    size = size_for_trade(self.settings, self.portfolio.bankroll, signal.asset, signal.best_ask)
                    notional = size * signal.best_ask
                    limit = check_limits(self.settings, self.portfolio, signal, notional, now)
                    self.store.save_signal(signal, limit.approved, limit.reason)
                    if not limit.approved:
                        recent_rejections.append(f"{signal.market_id}:{limit.reason}")
                        continue

                    req = OrderRequest(signal.market_id, signal.favorite_side, size, signal.best_ask, True)
                    outcome = self.router.submit_paper(req, book, now, now)
                    self.store.save_order(outcome.order_id, now, signal.market_id, True, outcome.status, outcome.fill.reason, size, signal.best_ask, outcome.fill.fill_price, outcome.fill.fill_size)
                    if outcome.status != "filled" or outcome.fill.fill_price is None:
                        recent_rejections.append(f"{signal.market_id}:entry_{outcome.fill.reason}")
                        continue

                    position = Position(
                        position_id=str(uuid.uuid4()),
                        market_id=signal.market_id,
                        asset=signal.asset,
                        horizon=signal.horizon,
                        side=signal.favorite_side,
                        entry_price=outcome.fill.fill_price,
                        entry_size=outcome.fill.fill_size,
                        target_price=self.settings.tp_price,
                        stop_price=self.settings.sl_price,
                        time_stop_threshold=self.settings.time_stop_seconds,
                    )
                    self.portfolio.open_positions[position.market_id] = position
                    self.store.upsert_position(position)

                for market_id, position in list(self.portfolio.open_positions.items()):
                    market = tracked.get(market_id)
                    if market is None:
                        continue
                    book = self.marketdata.get_book(market)
                    secs = market.seconds_to_expiry(now)
                    exit_check = check_exit(self.settings, position, book, secs)
                    if not exit_check.should_exit or exit_check.limit_price is None:
                        continue
                    req = OrderRequest(position.market_id, position.side, position.entry_size, exit_check.limit_price, False)
                    outcome = self.router.submit_paper(req, book, now, now)
                    self.store.save_order(outcome.order_id, now, position.market_id, False, outcome.status, outcome.fill.reason, position.entry_size, exit_check.limit_price, outcome.fill.fill_price, outcome.fill.fill_size)
                    if outcome.status != "filled" or outcome.fill.fill_price is None:
                        continue
                    position.status = PositionStatus.CLOSED
                    position.exit_time = now
                    position.exit_reason = exit_check.reason
                    position.realized_pnl = (outcome.fill.fill_price - position.entry_price) * outcome.fill.fill_size
                    self.portfolio.closed_positions.append(position)
                    self.portfolio.last_exit_by_market[position.market_id] = now
                    del self.portfolio.open_positions[position.market_id]
                    self.store.upsert_position(position)

                enabled_lanes = [
                    lane
                    for lane in ["BTC_5M", "BTC_15M", "ETH_5M", "ETH_15M", "SOL_5M", "SOL_15M"]
                    if getattr(self.settings, f"enable_{lane.lower()}", False)
                ]
                LOGGER.info("\n%s", render_dashboard(self.settings.mode.value, enabled_lanes, self.portfolio, len(candidates), recent_rejections))
                time.sleep(self.settings.poll_interval_ms / 1000)
        except KeyboardInterrupt:
            LOGGER.info("graceful shutdown requested")
            self.running = False
        finally:
            LOGGER.info("runtime stopped")
