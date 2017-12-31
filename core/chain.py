from core.block import HashedBlock
from core.chain_storage import BlockChainStorage
from core.config import LOG_PATH
from core.dblog import DBLogger
from core import difficulty
from core.difficulty import DEFAULT_DIFFICULTY, difficulty_adjustment
from typing import Dict, Iterator, Optional, List

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
        self.l = DBLogger(self, LOG_PATH)

    @staticmethod
    def load(storage: BlockChainStorage) -> "BlockChain":
        genesis = storage.get_genesis()
        if genesis is None:
            raise NoGenesisBlockError("No genesis block in storage")

        bc = BlockChain(genesis, storage)
        bc.l.info("Loading existing chain, validating blocks")
        for b in storage.get_all_non_genesis_in_order():
            bc.validate_block(b)
        bc.l.info("All blocks validated")
        return bc

    @staticmethod
    def new(storage: BlockChainStorage, genesis_block: HashedBlock) -> "BlockChain":
        if storage.get_genesis() is not None:
            raise MultipleGenesisBlockError("Already have a genesis block in storage!")

        storage.add_block(genesis_block)
        bc = BlockChain(genesis_block, storage)

        bc.l.info("New chain, added genesis {} to storage".format(
            genesis_block.mining_hash().hex()))
        return bc

    def get_difficulty(self, head: Optional[HashedBlock] = None) -> int:
        if head is None:
            h = self.get_head()
        else:
            h = head

        if (h.block_num() + 1) < TUNING_SEGMENT_LENGTH:
            return difficulty.DEFAULT_DIFFICULTY
        elif (h.block_num() + 1) % TUNING_SEGMENT_LENGTH == 0:
            diff = self.tuning_segment_difficulty(
                    h.block.block_config.difficulty, h.block_num())
            self.l.info("Head ({}) is at end of segment, retune to {}".format(
                h.block_num(), diff))
            return diff
        else:
            return h.block.block_config.difficulty

    def get_head(self) -> HashedBlock:
        return self.storage.get_head()

    def add_block(self, block: HashedBlock) -> None:
        self.validate_block(block)
        self.l.debug("Store block", block.block_num(), block.mining_hash().hex())
        self.storage.add_block(block)

    def validate_block(self, block: HashedBlock) -> None:
        if not self.storage.has_hash(block.parent_mining_hash()):
            raise UnknownParentError(
                "Parent with hash {} not known".format(
                    block.parent_mining_hash()))

        parent = self.storage.get_by_hash(block.parent_mining_hash())
        difficulty = self.get_difficulty(parent)

        if block.block.block_config.difficulty != difficulty:
            raise DifficultyMismatchError(
                "Unexpected difficulty {} for block {} ({}), expected {}".format(
                    block.block.block_config.difficulty,
                    block.block_num(),
                    block.mining_hash().hex(),
                    difficulty))

    def tuning_segment_difficulty(self, current_difficulty: int, height: int) -> int:
        self.l.debug("Calculating tuning segment difficulty using height", height)

        seg_stop = ((height // TUNING_SEGMENT_LENGTH) + 1) * TUNING_SEGMENT_LENGTH
        seg_start = seg_stop - TUNING_SEGMENT_LENGTH
        self.l.debug("Getting segment [{}, {})".format(seg_start, seg_stop))

        segment = self.storage.get_range(seg_start, seg_stop)
        times = map(lambda b: b.mining_timestamp, segment)
        adjustment = difficulty_adjustment(times)
        new_difficulty = current_difficulty + adjustment
        self.l.debug("Tuning difficulty:", new_difficulty)

        return new_difficulty
