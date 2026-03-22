from enum import Enum


class Asset(str, Enum):
    BTC = "BTC"
    ETH = "ETH"
    SOL = "SOL"


class Horizon(str, Enum):
    M5 = "5m"
    M15 = "15m"


class Side(str, Enum):
    YES = "YES"
    NO = "NO"


class Mode(str, Enum):
    PAPER = "paper"
    LIVE = "live"


class PositionStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"


class ExitReason(str, Enum):
    TAKE_PROFIT = "take_profit"
    STOP_LOSS = "stop_loss"
    TIME_STOP = "time_stop"
    RESOLUTION = "resolution"
    MANUAL = "manual"
