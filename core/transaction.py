from core.amount import Amount
from core.key_pair import Address, KeyPair
from core.serializable import Serializable, Ser
from core.signature import Signature
from core.timestamp import Timestamp
from typing import Optional

class Transaction(Serializable):
    def __init__(
            self,
            amount: Amount,
            timestamp: Timestamp,
            from_addr: Optional[Address],
            to_addr: Address) -> None:
        self.amount = amount
        self.timestamp = timestamp
        self.from_addr = from_addr
        self.to_addr = to_addr

    def serializable(self) -> Ser:
        from_addr = self.from_addr.serializable() if self.from_addr else None
        return {
            "amount": self.amount.serializable(),
            "timestamp": self.timestamp.serializable(),
            "from_addr": from_addr,
            "to_addr": self.to_addr.serializable(),
        }

    @staticmethod
    def from_dict(obj: Ser) -> 'Transaction':
        amt = Amount.from_dict(obj["amount"])
        t = Timestamp.from_dict(obj["timestamp"])
        if obj["from_addr"]:
            from_addr = Address.from_dict(obj["from_addr"])
        else:
            from_addr = None

        to_addr = Address.from_dict(obj["to_addr"])
        return Transaction(amt, t, from_addr, to_addr)

class SignedTransaction(Serializable):
    def __init__(self, transaction: Transaction, signature: Signature) -> None:
        self.transaction = transaction
        self.signature = signature

    @staticmethod
    def sign(transaction: Transaction, key_pair: KeyPair) -> "SignedTransaction":
        sig = key_pair.sign(transaction.serialize())
        return SignedTransaction(transaction, sig)

    def is_valid(self) -> bool:
        if self.transaction.from_addr is not None:
            verify_addr = self.transaction.from_addr
        else:
            verify_addr = self.transaction.to_addr

        return verify_addr.signature_is_valid(
                self.transaction.serialize(),
                self.signature)
    
    def serializable(self) -> Ser:
        return {
            "transaction": self.transaction.serializable(),
            "signature": self.signature.serializable(),
        }

    @staticmethod
    def from_dict(obj: Ser) -> 'SignedTransaction':
        txn = Transaction.from_dict(obj["transaction"])
        sig = Signature.from_dict(obj["signature"])
        return SignedTransaction(txn, sig)
