from core.serializable import Serializable, Ser
import time

class Timestamp(Serializable):
    def __init__(self, unix_millis: int) -> None:
        self.unix_millis = unix_millis

    @staticmethod
    def now() -> 'Timestamp':
        return Timestamp(int(time.time() * 1000))

    def serializable(self) -> Ser:
        return {
            "unix_millis": self.unix_millis
        }
