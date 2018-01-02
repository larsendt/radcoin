from core.key_pair import Address, KeyPair
from core.serializable import Serializable, Ser
from core.signature import Signature
from core.transaction.transaction import Transaction

class SignedTransaction(Serializable):
    def __init__(self, transaction: Transaction, signature: Signature) -> None:
        self.transaction = transaction
        self.signature = signature

    @staticmethod
    def sign(transaction: Transaction, key_pair: KeyPair) -> "SignedTransaction":
        sig = key_pair.sign(transaction.serialize())
        return SignedTransaction(transaction, sig)

    def is_reward(self) -> bool:
        return (len(self.transaction.inputs) == 0
                and len(self.transaction.outputs) == 1)

    def signature_is_valid(self) -> bool:
        return self.transaction.claimer.signature_is_valid(
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

