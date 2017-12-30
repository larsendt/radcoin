from core.miner import BlockMiner
from core.chain import BlockChain
from core.sqlite_chain import SqliteBlockChainStorage
import os

bm = BlockMiner()
storage = SqliteBlockChainStorage("db.sqlite")

if storage.get_genesis() is None:
    print("Making a new chain")
    genesis = bm.make_genesis()
    chain = BlockChain.new(storage, genesis)
else:
    print("Loading existing chain")
    chain = BlockChain.load(storage)

while True:
    head = chain.get_head()
    print("Mining on block {}".format(head.block_num()))
    new_block = bm.mine_on(head, chain.get_difficulty())
    print("Found block {} {}".format(new_block.block_num(), new_block.mining_hash().hex()))
    chain.add_block(new_block)
