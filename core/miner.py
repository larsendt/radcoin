from core.amount import Amount
from core.block import Block, HashedBlock
from core.block_config import BlockConfig
from core.coin import Coin
from core.key_pair import KeyPair
from core.timestamp import Timestamp
from core.transaction import Transaction, SignedTransaction
import os

class BlockMiner(object):
    def __init__(self) -> None:
        self.key_pair = KeyPair()

    def mine_on(self, parent: HashedBlock, difficulty: int) -> HashedBlock:
        reward = self.make_reward()
        config = BlockConfig(difficulty)
        block = Block(
            parent.block_num()+1,
            parent.mining_hash(),
            config,
            self.key_pair.address(),
            [reward])
        hb = HashedBlock(block)

        while not hb.hash_meets_difficulty():
            hb.replace_mining_entropy(os.urandom(32))
        return hb

    def make_reward(self) -> SignedTransaction:
        reward = Transaction(
                Amount.units(100, Coin.Radcoin),
                Timestamp.now(),
                None,
                self.key_pair.address())

        return SignedTransaction.sign(reward, self.key_pair)
