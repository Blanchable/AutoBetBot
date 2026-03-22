from collections import Counter, defaultdict
from dataclasses import dataclass

from app.config import Settings
from execution.exit_manager import check_exit
from execution.fill_manager import simulate_entry_fill, simulate_exit_fill
from models.book import MarketBook
from models.market import Market
from models.position import Position
from models.portfolio import PortfolioState
from risk.portfolio_limits import check_limits
from risk.sizing import size_for_trade
from strategies.favorite_momentum import evaluate_market, rank_signal
from utils.time_utils import utc_now


@dataclass(slots=True)
class BacktestResult:
    trade_count: int
    win_rate: float
    pnl_per_dollar: float
    avg_hold_seconds: float
    max_drawdown: float
    pnl_by_asset: dict[str, float]
    pnl_by_horizon: dict[str, float]
    rejection_counts: dict[str, int]


def run_replay(settings: Settings, timeline: list[tuple[Market, MarketBook]]) -> BacktestResult:
    portfolio = PortfolioState(bankroll=settings.bankroll)
    rejections: Counter[str] = Counter()
    pnl_curve = [0.0]
    pnl_by_asset = defaultdict(float)
    pnl_by_horizon = defaultdict(float)
    hold_times = []

    for market, book in timeline:
        now = utc_now()
        seconds_left = market.seconds_to_expiry(now)
        size = size_for_trade(settings, portfolio.bankroll, market.asset, max(book.yes.best_ask.price, book.no.best_ask.price))
        decision = evaluate_market(settings, market, book, seconds_left, size * settings.min_required_depth_multiple)
        if decision.candidate is None:
            rejections[decision.reason] += 1
            continue

        signal = decision.candidate
        rank_signal(signal)
        notional = size * signal.best_ask
        limit = check_limits(settings, portfolio, signal, notional, now)
        if not limit.approved:
            rejections[limit.reason] += 1
            continue

        entry_fill = simulate_entry_fill(book, signal.favorite_side, signal.best_ask, size, settings.paper_fill_model)
        if not entry_fill.filled or entry_fill.fill_price is None:
            rejections[entry_fill.reason] += 1
            continue

        position = Position(
            position_id=f"bt-{market.market_id}",
            market_id=market.market_id,
            asset=market.asset,
            horizon=market.horizon,
            side=signal.favorite_side,
            entry_price=entry_fill.fill_price,
            entry_size=entry_fill.fill_size,
            target_price=settings.tp_price,
            stop_price=settings.sl_price,
            time_stop_threshold=settings.time_stop_seconds,
        )
        exit_check = check_exit(settings, position, book, seconds_left)
        if not exit_check.should_exit or exit_check.limit_price is None:
            rejections["no_exit"] += 1
            continue

        exit_fill = simulate_exit_fill(book, position.side, exit_check.limit_price, position.entry_size)
        if not exit_fill.filled or exit_fill.fill_price is None:
            rejections[exit_fill.reason] += 1
            continue

        pnl = (exit_fill.fill_price - position.entry_price) * exit_fill.fill_size
        pnl_curve.append(pnl_curve[-1] + pnl)
        pnl_by_asset[position.asset.value] += pnl
        pnl_by_horizon[position.horizon.value] += pnl
        hold_times.append(max(0, seconds_left - settings.time_stop_seconds))

    trades = len(pnl_curve) - 1
    wins = sum(1 for i in range(1, len(pnl_curve)) if pnl_curve[i] > pnl_curve[i - 1])
    peak = -1e9
    mdd = 0.0
    for x in pnl_curve:
        peak = max(peak, x)
        mdd = min(mdd, x - peak)

    deployed = settings.bankroll if settings.bankroll > 0 else 1.0
    return BacktestResult(
        trade_count=trades,
        win_rate=(wins / trades) if trades else 0.0,
        pnl_per_dollar=(pnl_curve[-1] / deployed) if deployed else 0.0,
        avg_hold_seconds=(sum(hold_times) / len(hold_times)) if hold_times else 0.0,
        max_drawdown=abs(mdd),
        pnl_by_asset=dict(pnl_by_asset),
        pnl_by_horizon=dict(pnl_by_horizon),
        rejection_counts=dict(rejections),
    )
