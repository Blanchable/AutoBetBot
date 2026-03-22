from app.config import Settings
from models.enums import Asset


def size_for_trade(settings: Settings, bankroll: float, asset: Asset, ask_price: float) -> float:
    base_dollars = min(
        settings.max_position_size_dollars,
        bankroll * settings.max_position_size_fraction,
    )
    multiplier = {
        Asset.BTC: settings.btc_size_multiplier,
        Asset.ETH: settings.eth_size_multiplier,
        Asset.SOL: settings.sol_size_multiplier,
    }[asset]
    sized_dollars = max(0.0, base_dollars * multiplier)
    return round(sized_dollars / ask_price, 6) if ask_price > 0 else 0.0
