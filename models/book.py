from dataclasses import dataclass

from models.enums import Side


@dataclass(slots=True)
class BookLevel:
    price: float
    size: float


@dataclass(slots=True)
class SideBook:
    best_bid: BookLevel | None
    best_ask: BookLevel | None

    @property
    def midpoint(self) -> float | None:
        if self.best_bid is None or self.best_ask is None:
            return None
        return round((self.best_bid.price + self.best_ask.price) / 2, 4)

    @property
    def spread(self) -> float | None:
        if self.best_bid is None or self.best_ask is None:
            return None
        return round(max(0.0, self.best_ask.price - self.best_bid.price), 4)


@dataclass(slots=True)
class MarketBook:
    market_id: str
    yes: SideBook
    no: SideBook
    ts_epoch_ms: int

    def favorite_side(self) -> tuple[Side, SideBook] | None:
        yes_mid = self.yes.midpoint
        no_mid = self.no.midpoint
        if yes_mid is None and no_mid is None:
            return None
        if no_mid is None or (yes_mid is not None and yes_mid >= no_mid):
            return Side.YES, self.yes
        return Side.NO, self.no
