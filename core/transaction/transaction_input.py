from core.serializable import Hash, Serializable, Ser

class TransactionInput(Serializable):
    def __init__(self, output_block_hash: Hash, output_id: int) -> None:
        self.output_block_hash = output_block_hash
        self.output_id = output_id

    def serializable(self) -> Ser:
        return {
            "output_block_hash": self.output_block_hash.serializable(),
            "output_id": self.output_id,
        }

    @staticmethod
    def from_dict(obj: Ser) -> 'TransactionInput':
        return TransactionInput(obj["output_block_hash"], obj["output_id"])
