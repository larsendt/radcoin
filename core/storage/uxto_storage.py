from core.key_pair import Address
from core.serializable import Hash

class UXTO(object):
    def __init__(self, txn_hash: Hash, claimer_address: Address, output_id: int) -> None:
        self.txn_hash = txn_hash
        self.claimer_address = claimer_address
        self.output_id = output_id

class UXTOStorage(object):
    def __init__(self):
        pass

    def add_output(self, txn_hash: Hash, claimer_address: Address, output_id: int) -> None:
        raise NotImplementedError()

    def output_is_claimed(self, txn_hash: Hash, output_id: int) -> bool:
        raise NotImplementedError()

    def mark_claimed(self, txn_hash: Hash, output_id: int) -> None:
        raise NotImplementedError()
