from core.coin import Coin
from core.serializable import Serializable, Ser
from typing import Dict

NANOS_PER_UNIT = int(1e9)

class Amount(Serializable):
    def __init__(self, coin: Coin, amount_nanos: int) -> None:
        self.coin = coin
        self.nanos = amount_nanos

    @staticmethod
    def units(units: int, coin: Coin) -> "Amount":
        return Amount(coin, units * NANOS_PER_UNIT)

    def serializable(self) -> Ser:
        return {
            "nanos": self.nanos,
            "coin": self.coin.name
        }

    @staticmethod
    def from_dict(obj: Ser) -> "Amount":
        return Amount(Coin(obj["coin"]), obj["nanos"])
