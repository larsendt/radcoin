from core.block import HashedBlock
from core.storage.chain_storage import BlockChainStorage
from core.config import Config
from core.dblog import DBLogger
from core.serializable import Hash
from typing import List, Optional
import sqlite3

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS blocks (
    hash BLOB UNIQUE,
    parent_hash BLOB,
    block_num INTEGER,
    is_head INTEGER,
    serialized BLOB
)"""

CREATE_HASH_INDEX_SQL = """
CREATE UNIQUE INDEX IF NOT EXISTS hash_index ON blocks(hash)"""

CREATE_PARENT_HASH_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS parent_hash_index ON blocks(parent_hash)"""

CREATE_BLOCK_NUM_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS block_num_index ON blocks(block_num)"""

CREATE_HEAD_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS head_index ON blocks(is_head)"""

ADD_BLOCK_SQL = """
INSERT INTO blocks VALUES (
    :hash, :parent_hash, :block_num, :is_head, :serialized
)"""

GET_BY_HASH_SQL = "SELECT serialized FROM blocks WHERE hash = ?"
GET_BY_PARENT_HASH_SQL = "SELECT serialized FROM blocks WHERE parent_hash = ?"
GET_BY_NUM_SQL = "SELECT serialized FROM blocks WHERE block_num = ?"

GET_RANGE_SQL = """
SELECT serialized
FROM blocks
WHERE block_num >= :lower
AND block_num < :upper"""

GET_ALL_NON_GENESIS_IN_ORDER_SQL = """
SELECT serialized
FROM blocks
WHERE block_num > 0
ORDER BY block_num ASC"""

GET_HEIGHT_SQL = "SELECT MAX(block_num) FROM blocks"
GET_HEAD_SQL = "SELECT serialized FROM blocks WHERE is_head=1"

CLEAR_HEAD_SQL = "UPDATE blocks SET is_head=0 WHERE is_head=1"

class SqliteBlockChainStorage(BlockChainStorage):
    def __init__(self, cfg: Config) -> None:
        super().__init__()
        self.l = DBLogger(self, cfg)
        self._conn = sqlite3.connect(cfg.chain_db_path())
        with self._conn:
            cursor = self._conn.cursor()
            cursor.execute(CREATE_TABLE_SQL)
            cursor.execute(CREATE_HASH_INDEX_SQL)
            cursor.execute(CREATE_PARENT_HASH_INDEX_SQL)
            cursor.execute(CREATE_BLOCK_NUM_INDEX_SQL)
            cursor.execute(CREATE_HEAD_INDEX_SQL)

    def add_block(self, block: HashedBlock) -> None:
        c = self._conn.cursor()

        c.execute(GET_HEIGHT_SQL)
        height = c.fetchone()[0]

        if height is None:
            height = -1

        if block.block_num() > height:
            is_head = True
            c.execute(CLEAR_HEAD_SQL)
        else:
            is_head = False

        if block.parent_mining_hash() is None:
            parent_hash = None
        else:
            parent_hash = block.parent_mining_hash().raw_sha256

        args = {
            "hash": block.mining_hash().raw_sha256,
            "parent_hash": parent_hash,
            "block_num": block.block_num(),
            "is_head": is_head,
            "serialized": block.serialize(),
        }
        c.execute(ADD_BLOCK_SQL, args)
        self._conn.commit()

    def get_head(self) -> HashedBlock:
        c = self._conn.cursor()
        c.execute(GET_HEAD_SQL)
        res = c.fetchall()
        
        if len(res) == 0:
            raise Exception("No head")
        elif len(res) > 1:
            raise Exception("Multiple heads")
        else:
            return HashedBlock.deserialize(res[0][0])

    def get_height(self) -> int:
        c = self._conn.cursor()
        c.execute(GET_HEIGHT_SQL)
        res = c.fetchone()
        return res[0]

    def get_by_hash(self, block_hash: Hash) -> Optional[HashedBlock]:
        c = self._conn.cursor()
        c.execute(GET_BY_HASH_SQL, (block_hash.raw_sha256,))
        res = c.fetchone()
        if res:
            return HashedBlock.deserialize(res[0])
        else:
            return None

    def has_hash(self, block_hash: Hash) -> bool:
        c = self._conn.cursor()
        c.execute(GET_BY_HASH_SQL, (block_hash.raw_sha256,))
        return c.fetchone() is not None 

    def get_genesis(self) -> Optional[HashedBlock]:
        zero_blocks = list(self.get_by_block_num(0))
        if len(zero_blocks) > 1:
            raise Exception("More than one genesis block!")
        elif len(zero_blocks) == 0:
            return None
        else:
            return zero_blocks[0]

    def get_by_parent_hash(self, parent_hash: Hash) -> List[HashedBlock]:
        c = self._conn.cursor()
        c.execute(GET_BY_PARENT_HASH_SQL, (parent_hash.raw_sha256,))
        return list(map(lambda r: HashedBlock.deserialize(r[0]), c))

    def get_by_block_num(self, block_num: int) -> List[HashedBlock]:
        c = self._conn.cursor()
        c.execute(GET_BY_NUM_SQL, (block_num,))
        return list(map(lambda r: HashedBlock.deserialize(r[0]), c))

    def get_range(self, lower: int, upper: int) -> List[HashedBlock]:
        args = {
            "lower": lower,
            "upper": upper,
        }
        c = self._conn.cursor()
        c.execute(GET_RANGE_SQL, args)
        return list(map(lambda r: HashedBlock.deserialize(r[0]), c))

    def get_all_non_genesis_in_order(self) -> List[HashedBlock]:
        c = self._conn.cursor()
        c.execute(GET_ALL_NON_GENESIS_IN_ORDER_SQL)
        return list(map(lambda r: HashedBlock.deserialize(r[0]), c))
