from core.config import Config
from core.serializable import Hash
from core.storage.uxto_storage import UXTOStorage
import sqlite3

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS uxto (
    txn_hash BLOB,
    output_id INTEGER,
    claimed INTEGER
)"""

CREATE_INDEX_SQL = """
CREATE UNIQUE INDEX IF NOT EXISTS output_index
ON uxto(txn_hash, output_id)
"""

ADD_OUTPUT_SQL = """
INSERT INTO uxto VALUES (:txn_hash, :output_id, 0)
"""

OUTPUT_IS_CLAIMED_SQL = """
SELECT claimed
FROM uxto
AND txn_hash=:txn_hash
AND output_id=:output_id
"""

MARK_CLAIMED_SQL = """
UPDATE uxto
SET claimed=1
AND txn_hash=:txn_hash
AND output_id=:output_id
"""

class SqliteUXTOStorage(UXTOStorage):
    def __init__(self, cfg: Config) -> None:
        self._conn = sqlite3.connect(cfg.chain_db_path())

        self._conn.execute(CREATE_TABLE_SQL)
        self._conn.execute(CREATE_INDEX_SQL)
        self._conn.commit()

    def add_output(self, txn_hash: Hash, output_id: int) -> None:
        args = {
            "txn_hash": txn_hash.raw_sha256,
            "output_id": output_id,
        }
        self._conn.execute(ADD_OUTPUT_SQL, args)
        self._conn.commit()

    def output_is_claimed(self, txn_hash: Hash, output_id: int) -> bool:
        args = {
            "txn_hash": txn_hash.raw_sha256,
            "output_id": output_id,
        }
        c = self._conn.cursor()
        c.execute(OUTPUT_IS_CLAIMED_SQL, args)
        res = c.fetchone()

        if res is None:
            raise KeyError("Unmatched output", txn_hash, output_id)

        if res == 0:
            return False
        else:
            return True

    def mark_claimed(self, txn_hash: Hash, output_id: int) -> None:
        args = {
            "txn_hash": txn_hash.raw_sha256,
            "output_id": output_id,
        }
        self._conn.execute(MARK_CLAIMED_SQL, args)
        self._conn.commit()
