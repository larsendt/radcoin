from core.block import HashedBlock
from typing import List

class BlockChain(object):
    def __init__(self, genesis_block: HashedBlock) -> None:
        self.genesis_block = genesis_block
        self.blocks: List[HashedBlock] = [genesis_block]

    def get_head(self) -> HashedBlock:
        return self.blocks[-1]

    def add_block(self, block: HashedBlock) -> None:
        self.blocks.append(block)
