from core.block import HashedBlock
import os

class BlockMiner(object):
    def __init__(self) -> None:
        pass

    def mine(self, block: HashedBlock):
        while not block.hash_meets_difficulty():
            block.replace_mining_entropy(os.urandom(32))

        print("found hash! {}".format(block.mining_hash().hex()))



