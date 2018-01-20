from core.amount import Amount
from core.block import HashedBlock
from core.storage.chain_storage import BlockChainStorage
from core.storage.transaction_storage import TransactionStorage
from core.storage.uxto_storage import UXTOStorage 
from core.config import Config
from core.dblog import DBLogger
from core import difficulty
from core.difficulty import DEFAULT_DIFFICULTY, difficulty_adjustment
from core.serializable import Hash
from core.transaction.signed_transaction import SignedTransaction
from core.transaction.transaction_output import TransactionOutput
from typing import Dict, Iterator, Optional, List

TUNING_SEGMENT_LENGTH = 64
ABANDONMENT_DEPTH = 10
REWARD_AMOUNT = Amount.units(100)

class InvalidBlockError(Exception):
    pass

class InvalidTransactionError(Exception):
    pass

class BlockChain(object):
    def __init__(
            self,
            storage: BlockChainStorage,
            transaction_storage: TransactionStorage,
            uxto_storage: UXTOStorage,
            cfg: Config) -> None:

        self.storage = storage
        self.transaction_storage = transaction_storage
        self.uxto_storage = uxto_storage
        self.l = DBLogger(self, cfg)

        genesis = storage.get_genesis()
        if genesis is None:
            self.l.info("Storage didn't have genesis. Added.")
            storage.add_block(HashedBlock.genesis())

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
        if self.storage.has_hash(block.mining_hash()):
            self.l.debug("Already have block", block)
            return
        elif self.block_is_valid(block):
            self.l.debug("Store block", block)
            self.storage.add_block(block)
            for txn in block.block.transactions:
                for out in txn.transaction.outputs:
                    self.l.debug("Add UXTO", txn.txn_hash(), out.output_id)
                    self.uxto_storage.add_output(txn.txn_hash(), out.to_addr, out.output_id)

                for inp in txn.transaction.inputs:
                    out = self.get_transaction_output(
                        inp.output_block_hash,
                        inp.output_transaction_hash,
                        inp.output_id)

                    self.l.debug("Claim UXTO",
                        inp.output_transaction_hash,
                        inp.output_id)

                    self.uxto_storage.mark_claimed(
                        inp.output_transaction_hash,
                        inp.output_id)

            self._cleanup_outstanding_transactions(block)
            self._abandon_blocks()
        else:
            raise InvalidBlockError("Block is invalid")

    def add_outstanding_transaction(self, txn: SignedTransaction) -> None:
        if self.transaction_storage.has_transaction(txn.txn_hash()):
            self.l.debug("Already have txn", txn)
            return
        elif self.transaction_is_valid(txn):
            self.l.debug("Store transaction", txn)
            self.transaction_storage.add_transaction(txn)
        else:
            raise InvalidTransactionError("Transaction is invalid")

    @staticmethod
    def genesis_is_valid(block: HashedBlock, l: DBLogger) -> bool:
        return block.mining_hash() == HashedBlock.genesis().mining_hash()

    def block_is_valid(self, block: HashedBlock) -> bool:
        if self.storage.has_hash(block.parent_mining_hash()):
            parent = self.storage.get_by_hash(block.parent_mining_hash())
        else:
            self.l.warn("Parent with hash {} not known".format(
                block.parent_mining_hash().hex()))
            return False

        if self.block_should_be_abandoned(block):
            self.l.warn("Block should be abandoned", block)
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
        if signed.is_reward():
            return self.reward_is_valid(signed)

        if not signed.signature_is_valid():
            self.l.warn(
                "Transaction signature is invalid (sig {})".format(
                    signed.signature))
            return False

        output_sum = Amount(0)
        for output in signed.transaction.outputs:
            output_sum += output.amount

        claimed_prev_outputs: List[TransactionOutput] = []
        claimed_sum = Amount(0)
        for inp in signed.transaction.inputs:
            out = self.get_transaction_output(
                inp.output_block_hash,
                inp.output_transaction_hash,
                inp.output_id)
            
            if out is None:
                self.l.warn("Output was unknown", out)
                return False

            if self.uxto_storage.output_is_claimed(
                    inp.output_transaction_hash, inp.output_id):
                self.l.warn("Output already claimed", out)
                return False

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
        if not reward.signature_is_valid():
            self.l.warn(
                "Reward signature is invalid (sig {})".format(
                    reward.signature))
            return False

        if len(reward.transaction.outputs) != 1:
            self.l.warn("Reward has n_outputs != 1", reward)
            return False

        if len(reward.transaction.inputs) != 0:
            self.l.warn("Reward has inputs", reward)
            return False

        if reward.transaction.outputs[0].amount != REWARD_AMOUNT:
            self.l.warn("Reward has invalid amout", reward)
            return False

        return True

    def get_transaction_output(
        self,
        block_hash: Hash,
        txn_hash: Hash,
        output_id: int) -> Optional[TransactionOutput]:

        block = self.storage.get_by_hash(block_hash)

        if block is None:
            self.l.warn(
                "Don't have block hash {} when getting txn output".format(
                    block_hash.hex()))
            return None

        for signed in block.block.transactions:
            if signed.txn_hash() != txn_hash:
                continue 

            for output in signed.transaction.outputs:
                if output.output_id == output_id:
                    return output

        self.l.warn("No output with ID", output_id)
        return None

    def tuning_segment_difficulty(self, current_difficulty: int, height: int) -> int:
        self.l.debug("Calculating tuning segment difficulty using height", height)

        seg_stop = ((height // TUNING_SEGMENT_LENGTH) + 1) * TUNING_SEGMENT_LENGTH
        seg_start = seg_stop - TUNING_SEGMENT_LENGTH

        if seg_start == 0:
            self.l.debug("Omitting genesis block from tuning calculation")
            seg_start = 1

        self.l.debug("Getting segment [{}, {})".format(seg_start, seg_stop))

        segment = self.storage.get_range(seg_start, seg_stop)
        times = map(lambda b: b.mining_timestamp, segment)
        adjustment = difficulty_adjustment(times, self.l)
        new_difficulty = current_difficulty + adjustment
        self.l.debug("Tuning difficulty:", new_difficulty)

        if new_difficulty < 0:
            self.l.warn("Attempted to set new difficulty to {}, clamping to 0".format(new_difficulty))
            new_difficulty = 0
        elif new_difficulty > 255:
            self.l.warn("Attempted to set new difficulty to {}, clamping to 255".format(new_difficulty))
            new_difficulty = 255

        return new_difficulty

    def block_should_be_abandoned(self, block: HashedBlock) -> bool:
        """
        Either the block is in the master chain or it's within 10 blocks of
        the current head.
        """
        return not (self.block_is_in_master_chain(block)
                or (self.get_head().block_num() - block.block_num() < ABANDONMENT_DEPTH))
        
    def block_is_in_master_chain(self, block: HashedBlock) -> bool:
        """
        Use BFS to see if the current head can be reached from the block in 
        question.
        """
        head = self.get_head()
        crawl_queue: List[HashedBlock] = [block]

        while len(crawl_queue) > 0:
            cur = crawl_queue.pop(0)
            if cur == head:
                return True
            else:
                crawl_queue.extend(
                        self.storage.get_by_parent_hash(cur.mining_hash()))

        return False

    def _cleanup_outstanding_transactions(self, block: HashedBlock) -> None:
        self.l.debug("Cleaning up outstanding transactions in block", block)
        for txn in block.block.transactions:
            if self.transaction_storage.has_transaction(txn.txn_hash()):
                self.l.debug("Removing outstanding transaction", txn)
                self.transaction_storage.remove_transaction(txn.txn_hash())
            else:
                self.l.debug("Transaction wasn't oustanding", txn)

    def _abandon_blocks(self):
        head = self.get_head()
        abandon_height = head.block_num() - ABANDONMENT_DEPTH
        abandon_candidates = self.storage.get_by_block_num(abandon_height)
        for block in abandon_candidates:
            if self.block_should_be_abandoned(block):
                self.l.debug("Abandon block", block)
                self.storage.abandon_block(block)

                for txn in block.block.transactions:
                    if self.transaction_is_valid(txn):
                        self.l.debug("Adding abandoned transaction back to pool", txn)
                        self.transaction_storage.add_transaction(txn)
                    else:
                        self.l.debug("Abandoned transaction no longer valid")
