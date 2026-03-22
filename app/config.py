from dataclasses import dataclass
import os

from models.enums import Mode


@dataclass(slots=True)
class Settings:
    mode: Mode = Mode(os.getenv("MODE", "paper"))
    poll_interval_ms: int = int(os.getenv("POLL_INTERVAL_MS", "1000"))
    discovery_interval_sec: int = int(os.getenv("DISCOVERY_INTERVAL_SEC", "30"))
    sqlite_path: str = os.getenv("SQLITE_PATH", "autobetbot.db")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    enable_btc_5m: bool = os.getenv("ENABLE_BTC_5M", "1") == "1"
    enable_btc_15m: bool = os.getenv("ENABLE_BTC_15M", "1") == "1"
    enable_eth_5m: bool = os.getenv("ENABLE_ETH_5M", "1") == "1"
    enable_eth_15m: bool = os.getenv("ENABLE_ETH_15M", "1") == "1"
    enable_sol_5m: bool = os.getenv("ENABLE_SOL_5M", "1") == "1"
    enable_sol_15m: bool = os.getenv("ENABLE_SOL_15M", "1") == "1"

    entry_mid_min: float = float(os.getenv("ENTRY_MID_MIN", "0.85"))
    entry_ask_max: float = float(os.getenv("ENTRY_ASK_MAX", "0.86"))
    max_spread: float = float(os.getenv("MAX_SPREAD", "0.02"))
    min_seconds_left_5m: int = int(os.getenv("MIN_SECONDS_LEFT_5M", "45"))
    max_seconds_left_5m: int = int(os.getenv("MAX_SECONDS_LEFT_5M", "240"))
    min_seconds_left_15m: int = int(os.getenv("MIN_SECONDS_LEFT_15M", "60"))
    max_seconds_left_15m: int = int(os.getenv("MAX_SECONDS_LEFT_15M", "720"))

    tp_price: float = float(os.getenv("TP_PRICE", "0.95"))
    sl_price: float = float(os.getenv("SL_PRICE", "0.75"))
    time_stop_seconds: int = int(os.getenv("TIME_STOP_SECONDS", "20"))

    max_open_positions_global: int = int(os.getenv("MAX_OPEN_POSITIONS_GLOBAL", "4"))
    max_open_positions_per_asset: int = int(os.getenv("MAX_OPEN_POSITIONS_PER_ASSET", "2"))
    max_open_positions_per_horizon: int = int(os.getenv("MAX_OPEN_POSITIONS_PER_HORIZON", "3"))
    max_capital_deployed_fraction: float = float(os.getenv("MAX_CAPITAL_DEPLOYED_FRACTION", "0.4"))
    max_position_size_dollars: float = float(os.getenv("MAX_POSITION_SIZE_DOLLARS", "150"))
    max_position_size_fraction: float = float(os.getenv("MAX_POSITION_SIZE_FRACTION", "0.05"))
    cooldown_seconds_after_exit: int = int(os.getenv("COOLDOWN_SECONDS_AFTER_EXIT", "45"))
    btc_size_multiplier: float = float(os.getenv("BTC_SIZE_MULTIPLIER", "0.5"))
    eth_size_multiplier: float = float(os.getenv("ETH_SIZE_MULTIPLIER", "1.0"))
    sol_size_multiplier: float = float(os.getenv("SOL_SIZE_MULTIPLIER", "1.0"))

    entry_order_timeout_sec: int = int(os.getenv("ENTRY_ORDER_TIMEOUT_SEC", "6"))
    exit_order_timeout_sec: int = int(os.getenv("EXIT_ORDER_TIMEOUT_SEC", "4"))
    min_required_depth_multiple: float = float(os.getenv("MIN_REQUIRED_DEPTH_MULTIPLE", "1.2"))
    paper_fill_model: str = os.getenv("PAPER_FILL_MODEL", "conservative")

    bankroll: float = float(os.getenv("BANKROLL", "2000"))
    stale_data_ms: int = int(os.getenv("STALE_DATA_MS", "5000"))
