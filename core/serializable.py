import hashlib
import json
from typing import Any, Dict

Ser = Dict[str, Any] # would like to have Dict[str, Union['Ser', str]] here

class Serializable(object):
    def serializable(self) -> Ser:
        raise NotImplementedError("Implement this, dummy")

    @staticmethod
    def from_dict(obj: Ser) -> Any:
        raise NotImplementedError("Implement this, dummy")

    @classmethod
    def deserialize(cls, payload: bytes) -> Any:
        obj = json.loads(payload)
        return cls.from_dict(obj)

    def serialize(self) -> bytes:
        obj = self.serializable()
        return json.dumps(obj, sort_keys=True).encode("utf-8")

    def sha256(self) -> 'Hash':
        ser = self.serialize()
        m = hashlib.sha256()
        m.update(ser)
        return Hash(m.digest())

class Hash(Serializable):
    def __init__(self, raw_sha256: bytes) -> None:
        self.raw_sha256 = raw_sha256

    @staticmethod
    def fromhex(hash_hex: str) -> 'Hash':
        return Hash(bytes.fromhex(hash_hex))

    def hex(self) -> str:
        return self.raw_sha256.hex()

    def __str__(self) -> str:
        return "Hash<hex_sha256={}>".format(self.raw_sha256)

    def serializable(self) -> Ser:
        return {
            "sha256_hex": self.hex(),
        }

    @staticmethod
    def from_dict(obj: Ser) -> 'Hash':
        return Hash(bytes.fromhex(obj["sha256_hex"]))

