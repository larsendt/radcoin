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

    def sha256(self) -> bytes:
        ser = self.serialize()
        m = hashlib.sha256()
        m.update(ser)
        return m.digest()
