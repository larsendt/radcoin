from core.serializable import Serializable, Ser
from typing import Dict

NANOS_PER_UNIT = int(1e9)

class Amount(Serializable):
    def __init__(self, amount_nanos: int) -> None:
        self.nanos = amount_nanos

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Amount):
            return self.nanos == other.nanos
        else:
            return False

    def __add__(self, other: object) -> 'Amount':
        if not isinstance(other, Amount):
            raise TypeError("idiot")

        return Amount(self.nanos + other.nanos)

    def __iadd__(self, other: object) -> 'Amount':
        if not isinstance(other, Amount):
            raise TypeError("idiot")

        self.nanos += other.nanos
        return self

    def __str__(self) -> str:
        return "Amount<{}RC>".format(self.nanos / NANOS_PER_UNIT)

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
