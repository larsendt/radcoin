import arrow
from core.serializable import Serializable, Ser
import time

class Timestamp(Serializable):
    def __init__(self, unix_millis: int) -> None:
        self.unix_millis = unix_millis

    def __str__(self) -> str:
        return "Timestamp<unix_millis={},fmt={}>".format(
            self.unix_millis, arrow.get(self.unix_millis).format())

    @staticmethod
    def now() -> 'Timestamp':
        return Timestamp(int(time.time() * 1000))

    def serializable(self) -> Ser:
        return {
            "unix_millis": self.unix_millis
        }

    @staticmethod
    def from_dict(obj: Ser) -> 'Timestamp':
        return Timestamp(obj["unix_millis"])
