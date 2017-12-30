from core.block import HashedBlock
from core.chain_storage import BlockChainStorage
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
        self.height = 0
        self.previous_difficulty = DEFAULT_DIFFICULTY
        self.current_difficulty = DEFAULT_DIFFICULTY
        self.master_chain: List[bytes] = self.make_master_chain(
                genesis_block.mining_hash())

    @staticmethod
    def load(storage: BlockChainStorage) -> "BlockChain":
        genesis = storage.get_genesis()
        if genesis is None:
            raise NoGenesisBlockError("No genesis block in storage")
        return BlockChain(genesis, storage)

    @staticmethod
    def new(storage: BlockChainStorage, genesis_block: HashedBlock) -> "BlockChain":
        if storage.get_genesis() is not None:
            raise MultipleGenesisBlockError("Already have a genesis block in storage!")

        storage.add_block(genesis_block)
        return BlockChain(genesis_block, storage)

    def get_difficulty(self) -> int:
        return self.current_difficulty

    def get_head(self) -> HashedBlock:
        return self.storage.get_by_hash(self.master_chain[-1])

    def add_block(self, block: HashedBlock) -> None:
        if not self.storage.has_hash(block.parent_mining_hash()):
            raise UnknownParentError(
                "Parent with hash {} not known".format(
                    block.parent_mining_hash()))

        if block.block_num() % TUNING_SEGMENT_LENGTH == 0:
            self.previous_difficulty = self.current_difficulty
            self.current_difficulty = self.tuning_segment_difficulty()
        elif block.block.block_config.difficulty != self.current_difficulty:
            raise DifficultyMismatchError(
                "Unexpected difficulty {} for block {}, expected {}".format(
                    block.block.block_config.difficulty,
                    block.mining_hash(),
                    self.current_difficulty))

        if self.height < block.block_num():
            self.height = block.block_num()

        if block.parent_mining_hash() != self.master_chain[-1]:
            self.master_chain = self.make_master_chain(block.mining_hash())

        self.master_chain.append(block.mining_hash())
        self.storage.add_block(block)

    def tuning_segment_difficulty(self) -> int:
        seg_stop = ((self.height // TUNING_SEGMENT_LENGTH) + 1) * TUNING_SEGMENT_LENGTH
        seg_start = seg_stop - TUNING_SEGMENT_LENGTH
        segment = self.master_chain[seg_start:seg_stop]
        times = map(lambda h: self.storage.get_by_hash(h).mining_timestamp, segment)
        adjustment = difficulty_adjustment(times)
        return self.previous_difficulty + adjustment

    def make_master_chain(self, head_hash: bytes) -> List[bytes]:
        chain: List[bytes] = []

        while self.storage.has_hash(head_hash):
            chain.append(head_hash)
            b = self.storage.get_by_hash(head_hash)
            head_hash = b.mining_hash()

            if b.block_num() == 0:
                return list(reversed(chain))

        raise KeyError(
            "No parent for {} when following chain to genesis".format(
                head_hash))
