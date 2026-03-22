from dataclasses import dataclass
import os

from models.enums import Mode


def _parse_mode(value: str) -> Mode:
    try:
        return Mode(value)
    except ValueError:
        return Mode.PAPER


def _as_bool(name: str, default: str = "1") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


@dataclass(slots=True)
class Settings:
    mode: Mode
    poll_interval_ms: int
    discovery_interval_sec: int
    sqlite_path: str
    log_level: str

    enable_btc_5m: bool
    enable_btc_15m: bool
    enable_eth_5m: bool
    enable_eth_15m: bool
    enable_sol_5m: bool
    enable_sol_15m: bool

    entry_mid_min: float
    entry_ask_max: float
    max_spread: float
    min_seconds_left_5m: int
    max_seconds_left_5m: int
    min_seconds_left_15m: int
    max_seconds_left_15m: int

    tp_price: float
    sl_price: float
    time_stop_seconds: int

    max_open_positions_global: int
    max_open_positions_per_asset: int
    max_open_positions_per_horizon: int
    max_capital_deployed_fraction: float
    max_position_size_dollars: float
    max_position_size_fraction: float
    cooldown_seconds_after_exit: int
    btc_size_multiplier: float
    eth_size_multiplier: float
    sol_size_multiplier: float

    entry_order_timeout_sec: int
    exit_order_timeout_sec: int
    min_required_depth_multiple: float
    paper_fill_model: str

    bankroll: float
    stale_data_ms: int

    polymarket_api_key: str
    polymarket_api_secret: str
    polymarket_passphrase: str

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            mode=_parse_mode(os.getenv("MODE", "paper")),
            poll_interval_ms=int(os.getenv("POLL_INTERVAL_MS", "1000")),
            discovery_interval_sec=int(os.getenv("DISCOVERY_INTERVAL_SEC", "30")),
            sqlite_path=os.getenv("SQLITE_PATH", "autobetbot.db"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            enable_btc_5m=_as_bool("ENABLE_BTC_5M", "1"),
            enable_btc_15m=_as_bool("ENABLE_BTC_15M", "1"),
            enable_eth_5m=_as_bool("ENABLE_ETH_5M", "1"),
            enable_eth_15m=_as_bool("ENABLE_ETH_15M", "1"),
            enable_sol_5m=_as_bool("ENABLE_SOL_5M", "1"),
            enable_sol_15m=_as_bool("ENABLE_SOL_15M", "1"),
            entry_mid_min=float(os.getenv("ENTRY_MID_MIN", "0.85")),
            entry_ask_max=float(os.getenv("ENTRY_ASK_MAX", "0.86")),
            max_spread=float(os.getenv("MAX_SPREAD", "0.02")),
            min_seconds_left_5m=int(os.getenv("MIN_SECONDS_LEFT_5M", "45")),
            max_seconds_left_5m=int(os.getenv("MAX_SECONDS_LEFT_5M", "240")),
            min_seconds_left_15m=int(os.getenv("MIN_SECONDS_LEFT_15M", "60")),
            max_seconds_left_15m=int(os.getenv("MAX_SECONDS_LEFT_15M", "720")),
            tp_price=float(os.getenv("TP_PRICE", "0.95")),
            sl_price=float(os.getenv("SL_PRICE", "0.75")),
            time_stop_seconds=int(os.getenv("TIME_STOP_SECONDS", "20")),
            max_open_positions_global=int(os.getenv("MAX_OPEN_POSITIONS_GLOBAL", "4")),
            max_open_positions_per_asset=int(os.getenv("MAX_OPEN_POSITIONS_PER_ASSET", "2")),
            max_open_positions_per_horizon=int(os.getenv("MAX_OPEN_POSITIONS_PER_HORIZON", "3")),
            max_capital_deployed_fraction=float(os.getenv("MAX_CAPITAL_DEPLOYED_FRACTION", "0.4")),
            max_position_size_dollars=float(os.getenv("MAX_POSITION_SIZE_DOLLARS", "150")),
            max_position_size_fraction=float(os.getenv("MAX_POSITION_SIZE_FRACTION", "0.05")),
            cooldown_seconds_after_exit=int(os.getenv("COOLDOWN_SECONDS_AFTER_EXIT", "45")),
            btc_size_multiplier=float(os.getenv("BTC_SIZE_MULTIPLIER", "0.5")),
            eth_size_multiplier=float(os.getenv("ETH_SIZE_MULTIPLIER", "1.0")),
            sol_size_multiplier=float(os.getenv("SOL_SIZE_MULTIPLIER", "1.0")),
            entry_order_timeout_sec=int(os.getenv("ENTRY_ORDER_TIMEOUT_SEC", "6")),
            exit_order_timeout_sec=int(os.getenv("EXIT_ORDER_TIMEOUT_SEC", "4")),
            min_required_depth_multiple=float(os.getenv("MIN_REQUIRED_DEPTH_MULTIPLE", "1.2")),
            paper_fill_model=os.getenv("PAPER_FILL_MODEL", "conservative"),
            bankroll=float(os.getenv("BANKROLL", "2000")),
            stale_data_ms=int(os.getenv("STALE_DATA_MS", "5000")),
            polymarket_api_key=os.getenv("POLYMARKET_API_KEY", ""),
            polymarket_api_secret=os.getenv("POLYMARKET_API_SECRET", ""),
            polymarket_passphrase=os.getenv("POLYMARKET_PASSPHRASE", ""),
        )
