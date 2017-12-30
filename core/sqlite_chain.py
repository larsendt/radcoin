from core.block import HashedBlock
from core.chain_storage import BlockChainStorage
from typing import Iterator, Optional
import sqlite3

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS block_chain (
    hash BLOB UNIQUE,
    parent_hash BLOB,
    block_num INTEGER,
    serialized BLOB
)"""

CREATE_HASH_INDEX_SQL = """
CREATE UNIQUE INDEX IF NOT EXISTS hash_index ON block_chain(hash)"""

CREATE_PARENT_HASH_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS parent_hash_index ON block_chain(parent_hash)"""

CREATE_BLOCK_NUM_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS block_num_index ON block_chain(block_num)"""

ADD_BLOCK_SQL = """
INSERT INTO block_chain VALUES (
    :hash, :parent_hash, :block_num, :serialized
)"""

GET_BY_HASH_SQL = "SELECT serialized FROM block_chain WHERE hash = ?"
GET_BY_PARENT_HASH_SQL = "SELECT serialized FROM block_chain WHERE parent_hash = ?"
GET_BY_NUM_SQL = "SELECT serialized FROM block_chain WHERE block_num = ?"

GET_RANGE_SQL = """
SELECT serialized
FROM block_chain
WHERE block_num >= :lower
AND block_num < :upper"""

GET_ALL_IN_ORDER_SQL = """
SELECT serialized
FROM block_chain
ORDER BY block_num ASC"""

class SqliteBlockChainStorage(BlockChainStorage):
    def __init__(self, db_path: str) -> None:
        super().__init__()
        self._path = db_path
        self._conn = sqlite3.connect(db_path)
        self._conn.execute(CREATE_TABLE_SQL)
        self._conn.execute(CREATE_HASH_INDEX_SQL)
        self._conn.execute(CREATE_PARENT_HASH_INDEX_SQL)
        self._conn.execute(CREATE_BLOCK_NUM_INDEX_SQL)
        self._conn.commit()

    def add_block(self, block: HashedBlock) -> None:
        args = {
            "hash": block.mining_hash(),
            "parent_hash": block.parent_mining_hash(),
            "block_num": block.block_num(),
            "serialized": block.serialize(),
        }

        self._conn.execute(ADD_BLOCK_SQL, args)
        self._conn.commit()

    def get_by_hash(self, block_hash: bytes) -> HashedBlock:
        c = self._conn.cursor()
        c.execute(GET_BY_HASH_SQL, (block_hash,))
        return HashedBlock.deserialize(c.fetchone()[0])

    def has_hash(self, block_hash: bytes) -> bool:
        c = self._conn.cursor()
        c.execute(GET_BY_HASH_SQL, (block_hash,))
        return c.fetchone() is not None 

    def get_genesis(self) -> Optional[HashedBlock]:
        zero_blocks = list(self.get_by_block_num(0))
        if len(zero_blocks) > 1:
            raise Exception("More than one genesis block!")
        elif len(zero_blocks) == 0:
            return None
        else:
            return zero_blocks[0]

    def get_by_parent_hash(self, parent_hash: bytes) -> Iterator[HashedBlock]:
        c = self._conn.cursor()
        c.execute(GET_BY_PARENT_HASH_SQL, (parent_hash,))
        return map(lambda r: HashedBlock.deserialize(r[0]), c)

    def get_by_block_num(self, block_num: int) -> Iterator[HashedBlock]:
        c = self._conn.cursor()
        c.execute(GET_BY_NUM_SQL, (block_num,))
        return map(lambda r: HashedBlock.deserialize(r[0]), c)

    def get_range(self, start: int, stop: int) -> Iterator[HashedBlock]:
        args = {
            "start": start,
            "stop": stop,
        }
        c = self._conn.cursor()
        c.execute(GET_RANGE_SQL, args)
        return map(lambda r: HashedBlock.deserialize(r[0]), c)

    def get_all_in_order(self) -> Iterator[HashedBlock]:
        c = self._conn.cursor()
        c.execute(GET_ALL_IN_ORDER_SQL)
        return map(lambda r: HashedBlock.deserialize(r[0]), c)
