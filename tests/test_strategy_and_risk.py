from datetime import datetime, timedelta, timezone

from app.config import Settings
from execution.exit_manager import check_exit
from execution.fill_manager import simulate_entry_fill
from models.book import BookLevel, MarketBook, SideBook
from models.enums import Asset, Horizon, Side
from models.market import Market
from models.portfolio import PortfolioState
from models.signal import CandidateSignal
from models.position import Position
from risk.portfolio_limits import check_limits
from strategies.favorite_momentum import evaluate_market, rank_signal


def _market(horizon: Horizon = Horizon.M5) -> Market:
    return Market(
        market_id="m1",
        asset=Asset.BTC,
        horizon=horizon,
        yes_token_id="y",
        no_token_id="n",
        end_time=datetime.now(timezone.utc) + timedelta(minutes=2),
    )


def _book(yes_bid=0.85, yes_ask=0.86, no_bid=0.13, no_ask=0.14, depth=500) -> MarketBook:
    return MarketBook(
        market_id="m1",
        yes=SideBook(BookLevel(yes_bid, depth), BookLevel(yes_ask, depth)),
        no=SideBook(BookLevel(no_bid, depth), BookLevel(no_ask, depth)),
        ts_epoch_ms=int(datetime.now(timezone.utc).timestamp() * 1000),
    )


def test_favorite_detection_and_spread():
    b = _book()
    side, side_book = b.favorite_side()
    assert side == Side.YES
    assert side_book.spread == 0.01


def test_seconds_to_expiry_filters():
    s = Settings.from_env()
    m = _market(Horizon.M5)
    d = evaluate_market(s, m, _book(), seconds_left=30, min_required_depth=10)
    assert d.candidate is None
    assert d.reason == "outside_time_window"


def test_entry_eligibility_logic_passes():
    s = Settings.from_env()
    m = _market(Horizon.M5)
    d = evaluate_market(s, m, _book(), seconds_left=120, min_required_depth=10)
    assert d.candidate is not None


def test_tp_sl_and_time_stop_logic():
    s = Settings.from_env()
    p = Position("p1", "m1", Asset.BTC, Horizon.M5, Side.YES, 0.86, 10, 0.95, 0.75, 20)
    tp = check_exit(s, p, _book(yes_bid=0.96, yes_ask=0.97), seconds_left=120)
    assert tp.should_exit and tp.reason.value == "take_profit"
    sl = check_exit(s, p, _book(yes_bid=0.74, yes_ask=0.75), seconds_left=120)
    assert sl.should_exit and sl.reason.value == "stop_loss"
    ts = check_exit(s, p, _book(yes_bid=0.85, yes_ask=0.86), seconds_left=10)
    assert ts.should_exit and ts.reason.value == "time_stop"


def test_ranking_logic():
    signal = CandidateSignal(
        asset=Asset.BTC,
        horizon=Horizon.M5,
        market_id="m1",
        favorite_side=Side.YES,
        favorite_midpoint=0.9,
        best_bid=0.89,
        best_ask=0.9,
        spread=0.01,
        best_ask_depth=300,
        seconds_to_expiry=200,
        entry_reason="x",
    )
    score = rank_signal(signal, concentration_penalty=0.5)
    assert score > 0


def test_portfolio_limit_and_cooldown_enforcement():
    s = Settings.from_env()
    portfolio = PortfolioState(bankroll=1000)
    signal = CandidateSignal(Asset.BTC, Horizon.M5, "m1", Side.YES, 0.9, 0.89, 0.9, 0.01, 300, 100, "ok")
    ok = check_limits(s, portfolio, signal, estimated_notional=50, now=datetime.now(timezone.utc))
    assert ok.approved
    portfolio.last_exit_by_market["m1"] = datetime.now(timezone.utc)
    denied = check_limits(s, portfolio, signal, estimated_notional=50, now=datetime.now(timezone.utc))
    assert not denied.approved
    assert denied.reason == "cooldown_seconds_after_exit"


def test_paper_fill_model_basics():
    b = _book(depth=20)
    full = simulate_entry_fill(b, Side.YES, 0.86, 10, model="conservative")
    assert full.filled
    partial = simulate_entry_fill(b, Side.YES, 0.86, 30, model="conservative")
    assert not partial.filled and partial.reason == "partial_depth_only"
