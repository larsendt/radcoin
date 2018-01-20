from core.amount import Amount
from core.block import Block, HashedBlock
from core.block_config import BlockConfig
from core.chain import BlockChain, REWARD_AMOUNT
from core.config import Config
from core.dblog import DBLogger
from core.difficulty import DEFAULT_DIFFICULTY
from core.key_pair import KeyPair
from core.network.client import ChainClient
from core.storage.sqlite_chain import SqliteBlockChainStorage
from core.storage.sqlite_transaction import SqliteTransactionStorage
from core.storage.sqlite_uxto import SqliteUXTOStorage
from core.timestamp import Timestamp
from core.transaction.transaction import Transaction
from core.transaction.signed_transaction import SignedTransaction
import os
import time
from typing import List, Optional

class BlockMiner(object):
    def __init__(self, cfg: Config, key_pair: Optional[KeyPair] = None) -> None:
        self.l = DBLogger(self, cfg)
        self.l.info("Init")
        self.cfg = cfg

        self.client = ChainClient(cfg)

        if key_pair is None:
            self.key_pair = KeyPair.new()
        else:
            self.key_pair = key_pair

        self.storage = SqliteBlockChainStorage(cfg)
        self.transaction_storage = SqliteTransactionStorage(cfg)
        self.uxto_storage = SqliteUXTOStorage(cfg)
        self.chain = BlockChain(
            self.storage,
            self.transaction_storage,
            self.uxto_storage,
            cfg)

    def mine_forever(self) -> None:
        self.l.info("Miner running")

        while True:
            head = self.chain.get_head()
            self.l.debug("Mining on block {}".format(head.block_num()))
            new_block = self.mine_on(head, self.chain.get_difficulty())

            if new_block:
                self.l.info("Found block {} {}".format(
                    new_block.block_num(), new_block.mining_hash().hex()))
                self.chain.add_block(new_block)
            elif head != self.chain.get_head():
                self.l.info("Preempted! Mining on new block", head)

    def mine_on(self, parent: HashedBlock, difficulty: int) -> Optional[HashedBlock]:
        reward = self.make_reward()
        config = BlockConfig(difficulty)

        txns = self.transaction_storage.get_all_transactions()
        txns.append(reward)

        self.l.debug("Mining on {} txns".format(len(txns)))

        block = Block(
            parent.block_num()+1,
            parent.mining_hash(),
            config,
            txns)

        hb = HashedBlock(block)

        start = time.time()
        while time.time() - start < 1.0:
            hb.replace_mining_entropy(os.urandom(32))
            if hb.hash_meets_difficulty():
                return hb

        return None

    def transactions(self) -> List[SignedTransaction]:
        candidate_txns = self.transaction_storage.get_all_transactions()
        mine_txns: List[SignedTransaction] = []

        for txn in candidate_txns:
            if self.chain.transaction_is_valid(txn):
                self.l.debug("Txn is is valid for mining", txn)
                mine_txns.append(txn)
            else:
                self.l.warn("Txn is not valid for mining", txn)

        mine_txns.append(self.make_reward())
        return mine_txns

    def make_reward(self) -> SignedTransaction:
        reward = Transaction.reward(REWARD_AMOUNT, self.key_pair.address())
        return SignedTransaction.sign(reward, self.key_pair)

    def make_genesis(self) -> HashedBlock:
        b = Block(
            0, # block num 
            None, # parent hash
            BlockConfig(DEFAULT_DIFFICULTY),
            [])
        hb = HashedBlock(b)
        while not hb.hash_meets_difficulty():
            hb.replace_mining_entropy(os.urandom(32))
        return hb
