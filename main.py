from core.amount import Amount
from core.block import Block, HashedBlock
from core.block_config import BlockConfig
from core.miner import BlockMiner
from core.chain import BlockChain
from core.coin import Coin
from core.difficulty import DEFAULT_DIFFICULTY
from core.key_pair import KeyPair
from core.sqlite_chain import SqliteBlockChainStorage
from core.transaction import Transaction, SignedTransaction
from core.timestamp import Timestamp
import os

bm = BlockMiner()
storage = SqliteBlockChainStorage("db.sqlite")

if storage.get_genesis() is None:
    print("Making a new chain")
    t = Transaction(Amount.units(1, Coin.Radcoin), Timestamp.now(), None, bm.key_pair.address())
    s = SignedTransaction.sign(t, bm.key_pair)
    genesis = HashedBlock(Block(0, None, BlockConfig(DEFAULT_DIFFICULTY), bm.key_pair.address(), [s]))
    chain = BlockChain.new(storage, genesis)
else:
    print("Loading existing chain")
    chain = BlockChain.load(storage)

while True:
    head = chain.get_head()
    new_block = bm.mine_on(head, chain.get_difficulty())
    print("Found block {} {}".format(new_block.block_num(), new_block.mining_hash().hex()))
    chain.add_block(new_block)
