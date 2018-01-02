from core.amount import Amount
from core.block import HashedBlock
from core.chain_storage import BlockChainStorage
from core.config import Config
from core.dblog import DBLogger
from core import difficulty
from core.difficulty import DEFAULT_DIFFICULTY, difficulty_adjustment
from core.serializable import Hash
from core.transaction.signed_transaction import SignedTransaction
from core.transaction.transaction_output import TransactionOutput
from typing import Dict, Iterator, Optional, List

TUNING_SEGMENT_LENGTH = 64

class InvalidBlockError(Exception):
    pass

class BlockChain(object):
    def __init__(
            self,
            genesis_block: HashedBlock,
            storage: BlockChainStorage,
            cfg: Config) -> None:

        self.storage = storage
        self.l = DBLogger(self, cfg)

    @staticmethod
    def load(storage: BlockChainStorage, cfg: Config) -> "BlockChain":
        genesis = storage.get_genesis()
        if genesis is None:
            raise Exception("No genesis block in storage")

        bc = BlockChain(genesis, storage, cfg)
        bc.l.info("Loading existing chain, validating blocks")
        for b in storage.get_all_non_genesis_in_order():
            if not bc.block_is_valid(b):
                raise InvalidBlockError("Invalid block:", b)
        bc.l.info("All blocks validated")
        return bc

    @staticmethod
    def new(
        storage: BlockChainStorage,
        genesis_block: HashedBlock,
        cfg: Config) -> "BlockChain":
        if storage.get_genesis() is not None:
            raise Exception("Already have a genesis block in storage!")

        storage.add_block(genesis_block)
        bc = BlockChain(genesis_block, storage, cfg)

        bc.l.info("New chain, added genesis {} to storage".format(
            genesis_block.mining_hash().hex()))
        return bc

    def get_difficulty(self, head: Optional[HashedBlock] = None) -> int:
        if head is None:
            h = self.get_head()
        else:
            h = head

        if (h.block_num() + 1) < TUNING_SEGMENT_LENGTH:
            return difficulty.DEFAULT_DIFFICULTY
        elif (h.block_num() + 1) % TUNING_SEGMENT_LENGTH == 0:
            diff = self.tuning_segment_difficulty(
                    h.block.block_config.difficulty, h.block_num())
            self.l.info("Head ({}) is at end of segment, retune to {}".format(
                h.block_num(), diff))
            return diff
        else:
            return h.block.block_config.difficulty

    def get_head(self) -> HashedBlock:
        return self.storage.get_head()

    def add_block(self, block: HashedBlock) -> None:
        if self.block_is_valid(block):
            self.l.debug("Store block", block.block_num(), block.mining_hash().hex())
            self.storage.add_block(block)
        else:
            raise InvalidBlockError("Block is invalid")

    @staticmethod
    def genesis_is_valid(block: HashedBlock, l: DBLogger) -> bool:
        if block.block_num() != 0:
            l.warn("block num is not zero")
            return False

        if not block.hash_meets_difficulty():
            l.warn("hash doesn't meet difficulty")
            return False

        if len(block.block.transactions) != 0:
            l.warn("genesis block has transactions")
            return False

        return True

    def block_is_valid(self, block: HashedBlock) -> bool:
        if self.storage.has_hash(block.parent_mining_hash()):
            parent = self.storage.get_by_hash(block.parent_mining_hash())
        else:
            self.l.warn("Parent with hash {} not known".format(
                block.parent_mining_hash().hex()))
            return False

        difficulty = self.get_difficulty(parent)
        if block.block.block_config.difficulty != difficulty:
            self.l.warn(
                "Unexpected difficulty {} for block {} ({}), expected {}".format(
                    block.block.block_config.difficulty,
                    block.block_num(),
                    block.mining_hash().hex(),
                    difficulty))
            return False

        if not block.hash_meets_difficulty():
            self.l.warn(
                "Block hash doesn't meet the set difficulty")
            return False

        if block.block_num() != parent.block_num() + 1:
            self.l.warn("Block number isn't parent+1")
            return False

        n_rewards = 0
        for transaction in block.block.transactions:
            if not self.transaction_is_valid(transaction):
                self.l.warn("Transaction is invalid")
                return False

            if transaction.is_reward():
                n_rewards += 1

        if n_rewards != 1:
            self.l.warn(
                "Invalid number of rewards ({}) in transaction w/ sig{}".format(
                    n_rewards,
                    transaction.signature))
            return False

        return True

    def transaction_is_valid(self, signed: SignedTransaction) -> bool:
        if not signed.signature_is_valid():
            self.l.warn(
                "Transaction signature is invalid (sig {})".format(
                    signed.signature))
            return False

        if signed.is_reward():
            return self.reward_is_valid(signed)

        output_sum = Amount(0)
        for output in signed.transaction.outputs:
            output_sum += output.amount

        claimed_prev_outputs: List[TransactionOutput] = []
        claimed_sum = Amount(0)
        for inp in signed.transaction.inputs:
            out = self.get_transaction_output(
                inp.output_block_hash, inp.output_id)
            claimed_sum += out.amount

            if out.to_addr != signed.transaction.claimer:
                self.l.warn(
                    "Output {} can't be claimed by address {}".format(
                        out, signed.transaction.claimer))
                return False

        if output_sum != claimed_sum:
            self.l.warn("Input/output amount mismatch {} != {}".format(
                output_sum, claimed_sum))
            return False

        return True

    def reward_is_valid(self, reward: SignedTransaction) -> bool:
        # TODO
        return True

    def get_transaction_output(
        self,
        block_hash: Hash,
        output_id: int) -> Optional[TransactionOutput]:

        block = self.storage.get_by_hash(block_hash)

        if block is None:
            self.l.warn(
                "Don't have block hash {} when getting txn output".format(
                    block_hash.hex()))
            return None

        for signed in block.block.transactions:
            for output in signed.transaction.outputs:
                if output.output_id == output_id:
                    return output

        self.l.warn("No output with ID", output_id)
        return None

    def tuning_segment_difficulty(self, current_difficulty: int, height: int) -> int:
        self.l.debug("Calculating tuning segment difficulty using height", height)

        seg_stop = ((height // TUNING_SEGMENT_LENGTH) + 1) * TUNING_SEGMENT_LENGTH
        seg_start = seg_stop - TUNING_SEGMENT_LENGTH
        self.l.debug("Getting segment [{}, {})".format(seg_start, seg_stop))

        segment = self.storage.get_range(seg_start, seg_stop)
        times = map(lambda b: b.mining_timestamp, segment)
        adjustment = difficulty_adjustment(times, self.l)
        new_difficulty = current_difficulty + adjustment
        self.l.debug("Tuning difficulty:", new_difficulty)

        return new_difficulty
