from core.amount import Amount
from core.key_pair import Address
from core.serializable import Serializable, Ser

class TransactionOutput(Serializable):
    def __init__(self, output_id: int, amount: Amount, to_addr: Address) -> None:
        self.output_id = output_id
        self.amount = amount
        self.to_addr = to_addr

    def serializable(self) -> Ser:
        return {
            "output_id": self.output_id,
            "amount": self.amount.serializable(),
            "to_addr": self.to_addr.serializable(),
        }

    @staticmethod
    def from_dict(obj: Ser) -> 'TransactionOutput':
        return TransactionOutput(
            obj["output_id"],
            obj["amount"],
            obj["to_addr"])
