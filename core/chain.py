from core.block import HashedBlock
from core.chain_storage import BlockChainStorage
from core.config import DB_PATH
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
        self.l = DBLogger(self, DB_PATH)

    @staticmethod
    def load(storage: BlockChainStorage) -> "BlockChain":
        genesis = storage.get_genesis()
        if genesis is None:
            raise NoGenesisBlockError("No genesis block in storage")

        bc = BlockChain(genesis, storage)
        prev_b = genesis
        bc.l.info("Loading existing chain, validating blocks")
        for b in storage.get_all_non_genesis_in_order():
            bc.validate_block(b, simulated_head=prev_b)
            prev_b = b
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
            self.l.info("Head ({}) is at end of segment, calculating retune".format(h.block_num()))
            return self.tuning_segment_difficulty(h.block.block_config.difficulty, h.block_num())
        else:
            return h.block.block_config.difficulty

    def get_head(self) -> HashedBlock:
        return self.storage.get_head()

    def add_block(self, block: HashedBlock) -> None:
        self.validate_block(block)
        self.l.info("Store block", block.block_num(), block.mining_hash().hex())
        self.storage.add_block(block)

    def validate_block(
        self,
        block: HashedBlock,
        simulated_head: Optional[HashedBlock] = None) -> None:

        if not self.storage.has_hash(block.parent_mining_hash()):
            raise UnknownParentError(
                "Parent with hash {} not known".format(
                    block.parent_mining_hash()))

        if simulated_head:
            difficulty = self.get_difficulty(simulated_head)
        else:
            difficulty = self.get_difficulty()

        if block.block.block_config.difficulty != difficulty:
            raise DifficultyMismatchError(
                "Unexpected difficulty {} for block {} ({}), expected {}".format(
                    block.block.block_config.difficulty,
                    block.block_num(),
                    block.mining_hash().hex(),
                    difficulty))

    def tuning_segment_difficulty(self, current_difficulty: int, height: int) -> int:
        self.l.info("Calculating tuning segment difficulty using height", height)

        seg_stop = ((height // TUNING_SEGMENT_LENGTH) + 1) * TUNING_SEGMENT_LENGTH
        seg_start = seg_stop - TUNING_SEGMENT_LENGTH
        self.l.info("Getting segment [{}, {})".format(seg_start, seg_stop))

        segment = self.storage.get_range(seg_start, seg_stop)
        times = map(lambda b: b.mining_timestamp, segment)
        adjustment = difficulty_adjustment(times)
        new_difficulty = current_difficulty + adjustment
        self.l.info("Tuning difficulty:", new_difficulty)

        return new_difficulty
