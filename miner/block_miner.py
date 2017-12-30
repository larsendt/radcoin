from core.amount import Amount
from core.block import Block, HashedBlock
from core.coin import Coin
from core.key_pair import KeyPair
from core.transaction import Transaction, SignedTransaction
import os

class BlockMiner(object):
    def __init__(self) -> None:
        self.key_pair = KeyPair()

    def mine_on(self, parent: HashedBlock) -> HashedBlock:
        reward = self.make_reward()
        block = Block(parent, self.key_pair.address(), [reward])
        hb = HashedBlock(block)

        while not hb.hash_meets_difficulty():
            hb.replace_mining_entropy(os.urandom(32))
        return hb

    def make_reward(self) -> SignedTransaction:
        reward = Transaction(
                Amount.units(100, Coin.Radcoin),
                None,
                self.key_pair.address())

        return SignedTransaction.sign(reward, self.key_pair)
