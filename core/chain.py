from core.block import HashedBlock
from core import difficulty
from core.difficulty import DEFAULT_DIFFICULTY, difficulty_adjustment
from typing import Dict, List

TUNING_SEGMENT_LENGTH = 64

class UnknownParentError(Exception):
    pass

class DifficultyMismatchError(Exception):
    pass

class BlockChain(object):
    def __init__(self, genesis_block: HashedBlock) -> None:
        self.height = 0
        self.previous_difficulty = DEFAULT_DIFFICULTY
        self.current_difficulty = DEFAULT_DIFFICULTY
        self.blocks: Dict[bytes, HashedBlock] = {
            genesis_block.mining_hash(): genesis_block
        }
        self.master_chain: List[bytes] = self.make_master_chain(
                genesis_block.mining_hash())

    def get_difficulty(self) -> int:
        return self.current_difficulty

    def get_head(self) -> HashedBlock:
        return self.blocks[self.master_chain[-1]]

    def add_block(self, block: HashedBlock) -> None:
        if block.parent().mining_hash() not in self.blocks:
            raise UnknownParentError(
                "Parent with hash {} not known".format(
                    block.parent().mining_hash()))

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

        if block.parent().mining_hash() != self.master_chain[-1]:
            self.master_chain = self.make_master_chain(block.mining_hash())

        self.master_chain.append(block.mining_hash())
        self.blocks[block.mining_hash()] = block

    def tuning_segment_difficulty(self) -> int:
        seg_stop = ((self.height // TUNING_SEGMENT_LENGTH) + 1) * TUNING_SEGMENT_LENGTH
        seg_start = seg_stop - TUNING_SEGMENT_LENGTH
        segment = self.master_chain[seg_start:seg_stop]
        times = map(lambda b: self.blocks[b].mining_timestamp, segment)
        adjustment = difficulty_adjustment(times)
        return self.previous_difficulty + adjustment

    def make_master_chain(self, head_hash: bytes) -> List[bytes]:
        chain: List[bytes] = []

        while head_hash in self.blocks:
            chain.append(head_hash)
            b = self.blocks[head_hash]
            head_hash = b.mining_hash()

            if b.block_num() == 0:
                return list(reversed(chain))

        raise KeyError(
            "No parent for {} when following chain to genesis".format(
                head_hash))
