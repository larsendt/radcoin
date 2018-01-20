from core.config import Config
from core.key_pair import Address
from core.serializable import Hash
from core.storage.uxto_storage import UXTOStorage, UXTO
import sqlite3
from typing import List

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS uxto (
    txn_hash BLOB,
    claimer_ed25519_pub_key_hex TEXT,
    output_id INTEGER,
    claimed INTEGER
)"""

CREATE_INDEX_SQL = """
CREATE UNIQUE INDEX IF NOT EXISTS output_index
ON uxto(txn_hash, output_id)
"""

ADD_OUTPUT_SQL = """
INSERT INTO uxto VALUES (:txn_hash, :claimer_ed25519_pub_key, :output_id, 0)
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

GET_UNCLAIMED_OUTPUTS_FOR_CLAIMER = """
SELECT txn_hash, output_id
FROM uxto
WHERE claimer_ed25519_pub_key_hex = :claimer_ed25519_pub_key_hex
AND claimed = 0
"""

class SqliteUXTOStorage(UXTOStorage):
    def __init__(self, cfg: Config) -> None:
        self._conn = sqlite3.connect(cfg.chain_db_path())

        self._conn.execute(CREATE_TABLE_SQL)
        self._conn.execute(CREATE_INDEX_SQL)
        self._conn.commit()

    def add_output(self, txn_hash: Hash, claimer_address: Address, output_id: int) -> None:
        args = {
            "txn_hash": txn_hash.raw_sha256,
            "claimer_ed25519_pub_key_hex": claimer_address.hex(),
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

    def unclaimed_outputs(self, address: Address) -> List[UXTO]:
        args = {"claimer_ed25519_pub_key_hex": address.hex()}
        c = self._conn.cursor()
        c.execute(GET_UNCLAIMED_OUTPUTS_FOR_CLAIMER, args)
        return list(map(lambda r: UXTO(r[0], address, r[1]), c))
