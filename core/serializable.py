import hashlib
import json
from typing import Any, Dict

Ser = Dict[str, Any] # would like to have Dict[str, Union['Ser', str]] here

class Serializable(object):
    def serializable(self) -> Ser:
        raise NotImplemented("Implement this, dummy")

    def serialize(self) -> bytes:
        obj = self.serializable()
        return json.dumps(obj, sort_keys=True).encode("utf-8")

    def sha256(self) -> bytes:
        ser = self.serialize()
        m = hashlib.sha256()
        m.update(ser)
        return m.digest()
