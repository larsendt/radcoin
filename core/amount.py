from core.serializable import Serializable, Ser
from typing import Dict

NANOS_PER_UNIT = int(1e9)

class Amount(Serializable):
    def __init__(self, amount_nanos: int) -> None:
        self.nanos = amount_nanos

    @staticmethod
    def units(units: int) -> "Amount":
        return Amount(units * NANOS_PER_UNIT)

    def serializable(self) -> Ser:
        return {
            "nanos": self.nanos,
        }

    @staticmethod
    def from_dict(obj: Ser) -> "Amount":
        return Amount(obj["nanos"])
