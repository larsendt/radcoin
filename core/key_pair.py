from core.serializable import Serializable, Ser
from core.signature import Signature
import nacl.encoding
import nacl.exceptions
import nacl.signing
from typing import Dict

class Address(Serializable):
    def __init__(self, verify_key: nacl.signing.VerifyKey) -> None:
        super().__init__()
        self._verify_key = verify_key

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Address):
            return self._verify_key == other._verify_key
        else:
            return False

    @staticmethod
    def from_hex(hex_verify_key: bytes) -> 'Address':
        key = nacl.signing.VerifyKey(
                hex_verify_key, nacl.encoding.RawEncoder())
        return Address(key)

    def hex(self) -> str:
        return self._verify_key.encode(encoder=nacl.encoding.RawEncoder()).hex()

    @staticmethod
    def from_dict(obj: Ser) -> 'Address':
        hex_key = obj["edd25519_pub_key"]
        key = nacl.signing.VerifyKey(hex_key, nacl.encoding.HexEncoder())
        return Address(key)

    def signature_is_valid(self, message: bytes, signature: Signature) -> bool:
        try:
            self._verify_key.verify(
                    message,
                    signature.ed25519_signature,
                    encoder=nacl.encoding.RawEncoder())
            return True
        except nacl.exceptions.BadSignatureError:
            return False

    def serializable(self) -> Ser:
        return {
            "edd25519_pub_key": self._verify_key.encode(
                encoder=nacl.encoding.RawEncoder()).hex(),
        }

class KeyPair(object):
    def __init__(self, key: nacl.signing.SigningKey) -> None:
        self._signing_key = key

    @staticmethod
    def from_seed(seed: bytes) -> 'KeyPair':
        signing_key = nacl.signing.SigningKey(seed)
        return KeyPair(signing_key)

    @staticmethod
    def new() -> 'KeyPair':
        signing_key = nacl.signing.SigningKey.generate()
        return KeyPair(signing_key) 

    def address(self) -> Address:
        return Address(self._signing_key.verify_key)

    def seed(self) -> bytes:
        return bytes(self._signing_key)

    def sign(self, payload: bytes) -> Signature:
        signed = self._signing_key.sign(payload)
        return Signature(signed.signature)
