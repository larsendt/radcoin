from core.config import Config
from core.dblog import DBLogger
from core.serializable import Hash
from core.storage.transaction_storage import TransactionStorage
from core.transaction.signed_transaction import SignedTransaction
import sqlite3
from typing import List, Optional

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS transactions (
    txn_hash BLOB UNIQUE,
    serialized BLOB
)
"""

CREATE_TXN_HASH_INDEX_SQL = """
CREATE UNIQUE INDEX IF NOT EXISTS txn_hash_index ON transactions(txn_hash)
"""

ADD_TRANSACTION_SQL = """
INSERT INTO transactions VALUES (:txn_hash, :serialized)
"""

GET_ALL_TRANSACTIONS_SQL = "SELECT serialized FROM transactions"

GET_TRANSACTION_SQL = """
SELECT serialized FROM transactions WHERE txn_hash=:txn_hash
"""

HAS_TRANSACTION_SQL = """
SELECT txn_hash FROM transactions WHERE txn_hash=:txn_hash
"""

REMOVE_TRANSACTION_SQL = """
DELETE FROM transactions WHERE txn_hash=:txn_hash
"""

class SqliteTransactionStorage(TransactionStorage):
    def __init__(self, cfg: Config) -> None:
        self.l = DBLogger(self, cfg)
        self._conn = sqlite3.connect(cfg.chain_db_path())

        c = self._conn.cursor()
        c.execute(CREATE_TABLE_SQL)
        c.execute(CREATE_TXN_HASH_INDEX_SQL)
        self._conn.commit()

    def add_transaction(self, txn: SignedTransaction) -> None:
        args = {
            "txn_hash": txn.sha256().raw_sha256,
            "serialized": txn.serialize(),
        }

        c = self._conn.cursor()
        c.execute(ADD_TRANSACTION_SQL, args)
        self._conn.commit()

    def remove_transaction(self, txn_hash: Hash) -> None:
        args = {"txn_hash": txn_hash.raw_sha256}
        c = self._conn.cursor()
        c.execute(REMOVE_TRANSACTION_SQL, args)
        self._conn.commit()


    def has_transaction(self, txn_hash: Hash) -> bool:
        args = {"txn_hash": txn_hash.raw_sha256}
        c = self._conn.cursor()
        c.execute(HAS_TRANSACTION_SQL, args)
        res = c.fetchone()
        return res != None

    def get_all_transactions(self) -> List[SignedTransaction]:
        c = self._conn.cursor()
        c.execute(GET_ALL_TRANSACTIONS_SQL)
        return list(map(lambda s: SignedTransaction.deserialize(s[0]), c))

    def get_transaction(self, txn_hash: Hash) -> Optional[SignedTransaction]:
        args = {"txn_hash": txn_hash.raw_sha256}
        c = self._conn.cursor()
        c.execute(GET_TRANSACTION_SQL, args)
        res = c.fetchone()
        if res is None:
            return None
        else:
            return SignedTransaction.deserialize(res[0])
