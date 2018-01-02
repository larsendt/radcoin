from core.amount import Amount
from core.key_pair import Address
from core.serializable import Serializable, Ser
from core.timestamp import Timestamp
from core.transaction.transaction_input import TransactionInput
from core.transaction.transaction_output import TransactionOutput
from typing import List, Optional

class Transaction(Serializable):
    def __init__(
            self,
            inputs: List[TransactionInput],
            outputs: List[TransactionOutput],
            timestamp: Timestamp,
            claimer: Address) -> None:

        self.inputs = inputs
        self.outputs = outputs
        self.timestamp = timestamp
        self.claimer = claimer

    @staticmethod
    def reward(amount: Amount, claimer: Address) -> 'Transaction':
        out = TransactionOutput(0, amount, claimer)
        return Transaction([], [out], Timestamp.now(), claimer)

    def serializable(self) -> Ser:
        return {
            "inputs": list(map(lambda ti: ti.serializable(), self.inputs)),
            "outputs": list(map(lambda to: to.serializable(), self.outputs)),
            "timestamp": self.timestamp.serializable(),
            "claimer": self.claimer.serializable(),
        }

    @staticmethod
    def from_dict(obj: Ser) -> 'Transaction':
        inputs = map(lambda ti: TransactionInput.from_dict(ti), obj["inputs"])
        outputs = map(lambda ti: TransactionOutput.from_dict(ti), obj["outputs"])
        return Transaction(
            list(inputs),
            list(outputs),
            Timestamp.from_dict(obj["timestamp"]),
            Address.from_dict(obj["claimer"]))
