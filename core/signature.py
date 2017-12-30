from core.serializable import Serializable, Ser
from typing import Dict

class Signature(Serializable):
    def __init__(self, edd25519_signature: bytes) -> None:
        self.ed25519_signature = edd25519_signature

    def serializable(self) -> Ser:
        return {
            "ed25519_signature": self.ed25519_signature.hex(),
        }

    @staticmethod
    def from_dict(obj: Ser) -> 'Signature':
        sig = bytes.fromhex(obj["ed25519_signature"])
        return Signature(sig)
