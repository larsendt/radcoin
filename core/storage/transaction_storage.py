from core.serializable import Hash
from core.transaction.signed_transaction import SignedTransaction
from typing import List, Optional

class TransactionStorage(object):
    def __init__(self):
        pass

    def add_transaction(self, txn: SignedTransaction) -> None:
        raise NotImplementedError()

    def remove_transaction(self, txn_hash: Hash) -> None:
        raise NotImplementedError()

    def has_transaction(self, txn_hash: Hash) -> bool:
        raise NotImplementedError()

    def get_all_transactions(self) -> List[SignedTransaction]:
        raise NotImplementedError()

    def get_transaction(self, txn_hash: Hash) -> Optional[SignedTransaction]:
        raise NotImplementedError()
