from core.amount import Amount
from core.block import Block, HashedBlock
from core.chain import BlockChain
from core.coin import Coin
from core.key_pair import KeyPair
from core.transaction import Transaction, SignedTransaction
from core.timestamp import Timestamp
from miner.block_miner import BlockMiner
import os

bm = BlockMiner()

t = Transaction(Amount.units(1, Coin.Radcoin), Timestamp.now(), None, bm.key_pair.address())
s = SignedTransaction.sign(t, bm.key_pair)
genesis = HashedBlock(Block(None, bm.key_pair.address(), [s]))

chain = BlockChain(genesis)

while True:
    head = chain.get_head()
    new_block = bm.mine_on(head)
    print("Found block {} {}".format(new_block.block_num(), new_block.mining_hash().hex()))
    chain.add_block(new_block)
