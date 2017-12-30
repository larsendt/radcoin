from core.block import HashedBlock
from core.chain_storage import BlockChainStorage
from core.config import DB_PATH
from core.dblog import DBLogger
from core import difficulty
from core.difficulty import DEFAULT_DIFFICULTY, difficulty_adjustment
from typing import Dict, Iterator, List

TUNING_SEGMENT_LENGTH = 64

class UnknownParentError(Exception):
    pass

class DifficultyMismatchError(Exception):
    pass

class NoGenesisBlockError(Exception):
    pass

class MultipleGenesisBlockError(Exception):
    pass

class BlockChain(object):
    def __init__(
            self,
            genesis_block: HashedBlock,
            storage: BlockChainStorage) -> None:

        self.storage = storage
        self.l = DBLogger(self, DB_PATH)

    @staticmethod
    def load(storage: BlockChainStorage) -> "BlockChain":
        genesis = storage.get_genesis()
        if genesis is None:
            raise NoGenesisBlockError("No genesis block in storage")
        bc = BlockChain(genesis, storage)
        return bc

    @staticmethod
    def new(storage: BlockChainStorage, genesis_block: HashedBlock) -> "BlockChain":
        if storage.get_genesis() is not None:
            raise MultipleGenesisBlockError("Already have a genesis block in storage!")

        storage.add_block(genesis_block)
        return BlockChain(genesis_block, storage)

    def get_difficulty(self) -> int:
        h = self.get_head()
        if (h.block_num() + 1) % TUNING_SEGMENT_LENGTH == 0:
            self.l.info("Head ({}) is at end of segment, calculating retune".format(h.block_num()))
            return self.tuning_segment_difficulty()
        else:
            return h.block.block_config.difficulty

    def get_head(self) -> HashedBlock:
        return self.storage.get_head()

    def add_block(self, block: HashedBlock) -> None:
        self._validate_block(block)
        self.l.info("Store block", block.block_num(), block.mining_hash().hex())
        self.storage.add_block(block)

    def _validate_block(self, block: HashedBlock) -> None:
        if not self.storage.has_hash(block.parent_mining_hash()):
            raise UnknownParentError(
                "Parent with hash {} not known".format(
                    block.parent_mining_hash()))

        if block.block.block_config.difficulty != self.get_difficulty():
            raise DifficultyMismatchError(
                "Unexpected difficulty {} for block {}, expected {}".format(
                    block.block.block_config.difficulty,
                    block.mining_hash(),
                    self.get_difficulty()))

    def tuning_segment_difficulty(self) -> int:
        current_difficulty = self.get_head().block.block_config.difficulty
        seg_stop = ((self.storage.get_height() // TUNING_SEGMENT_LENGTH) + 1) * TUNING_SEGMENT_LENGTH
        seg_start = seg_stop - TUNING_SEGMENT_LENGTH
        segment = self.storage.get_range(seg_start, seg_stop)
        times = map(lambda b: b.mining_timestamp, segment)
        adjustment = difficulty_adjustment(times)
        return current_difficulty + adjustment
