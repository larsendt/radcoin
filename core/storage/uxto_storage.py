from core.serializable import Hash

class UXTOStorage(object):
    def __init__(self):
        pass

    def add_output(self, txn_hash: Hash, output_id: int) -> None:
        raise NotImplementedError()

    def output_is_claimed(self, txn_hash: Hash, output_id: int) -> bool:
        raise NotImplementedError()

    def mark_claimed(self, txn_hash: Hash, output_id: int) -> None:
        raise NotImplementedError()
