from core.miner import BlockMiner
from core.chain import BlockChain
from core.config import DB_PATH
from core.dblog import DBLogger
from core.sqlite_chain import SqliteBlockChainStorage
import os

bm = BlockMiner()
storage = SqliteBlockChainStorage(DB_PATH)
l = DBLogger(__name__, DB_PATH)

if storage.get_genesis() is None:
    l.info("Making a new chain")
    genesis = bm.make_genesis()
    chain = BlockChain.new(storage, genesis)
else:
    l.info("Loading existing chain")
    chain = BlockChain.load(storage)

while True:
    head = chain.get_head()
    l.info("Mining on block {}".format(head.block_num()))
    new_block = bm.mine_on(head, chain.get_difficulty())
    l.info("Found block {} {}".format(new_block.block_num(), new_block.mining_hash().hex()))
    chain.add_block(new_block)
