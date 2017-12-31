from core.amount import Amount
from core.block import Block, HashedBlock
from core.block_config import BlockConfig
from core.chain import BlockChain
from core.coin import Coin
from core.config import DB_PATH, LOG_PATH
from core.dblog import DBLogger
from core.difficulty import DEFAULT_DIFFICULTY
from core.key_pair import KeyPair
from core.sqlite_chain import SqliteBlockChainStorage
from core.timestamp import Timestamp
from core.transaction import Transaction, SignedTransaction
import os
import time
from typing import Optional

class BlockMiner(object):
    def __init__(self, key_pair: Optional[KeyPair] = None) -> None:
        self.l = DBLogger(self, LOG_PATH)

        if key_pair is None:
            self.key_pair = KeyPair()
        else:
            self.key_pair = key_pair

        self.storage = SqliteBlockChainStorage(DB_PATH)
        self.chain: Optional[BlockChain] = None

        if self.storage.get_genesis() is None:
            self.l.info("Storage has no genesis, either bootstrap with the client or mine a genesis block")
        else:
            self.l.info("Loading existing chain")
            self.chain = BlockChain.load(self.storage)

    def mine_genesis(self) -> None:
        if self.storage.get_genesis() is None:
            self.l.info("Making a new chain")
            genesis = self.make_genesis()
            self.chain = BlockChain.new(self.storage, genesis)
        else:
            self.l.info("Storage already has genesis, no need to mine it")

    def mine_forever(self) -> None:
        while True:
            head = self.chain.get_head()
            self.l.debug("Mining on block {}".format(head.block_num()))
            new_block = self.mine_on(head, self.chain.get_difficulty())

            if new_block:
                self.l.info("Found block {} {}".format(
                    new_block.block_num(), new_block.mining_hash().hex()))
                self.chain.add_block(new_block)
            else:
                self.l.debug("Checking for new head")

    def mine_on(self, parent: HashedBlock, difficulty: int) -> Optional[HashedBlock]:
        reward = self.make_reward()
        config = BlockConfig(difficulty)
        block = Block(
            parent.block_num()+1,
            parent.mining_hash(),
            config,
            self.key_pair.address(),
            [reward])
        hb = HashedBlock(block)

        start = time.time()
        while time.time() - start < 1.0:
            hb.replace_mining_entropy(os.urandom(32))
            if hb.hash_meets_difficulty():
                return hb

        return None

    def make_reward(self) -> SignedTransaction:
        reward = Transaction(
                Amount.units(100, Coin.Radcoin),
                Timestamp.now(),
                None,
                self.key_pair.address())

        return SignedTransaction.sign(reward, self.key_pair)

    def make_genesis(self) -> HashedBlock:
        t = self.make_reward()
        b = Block(
            0, # block num 
            None, # parent hash
            BlockConfig(DEFAULT_DIFFICULTY),
            self.key_pair.address(),
            [t])
        return HashedBlock(b)

