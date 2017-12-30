from core.block_config import BlockConfig
from core.key_pair import Address
from core.serializable import Serializable, Ser
from core.timestamp import Timestamp
from core.transaction import SignedTransaction
import hashlib
from typing import List, Union

class Block(Serializable):
    def __init__(
            self,
            parent: Union['HashedBlock', None],
            mining_addr: Address,
            transactions: List[SignedTransaction]) -> None:

        if parent is None:
            self.block_num = 0
            self.block_config = BlockConfig.genesis()
        else:
            self.block_num = parent.block.block_num + 1
            self.block_config = BlockConfig()

        self.parent = parent
        self.mining_addr = mining_addr
        self.transactions = transactions

    def serializable(self) -> Ser:
        txns = map(lambda t: t.serializable(), self.transactions)
        
        if self.parent is None:
            parent_hash = None
        else:
            parent_hash = self.parent.mining_hash().hex()

        return {
            "block_num": self.block_num,
            "parent_mined_hash": parent_hash,
            "miner_address": self.mining_addr.serializable(),
            "transactions": list(txns),
            "config": self.block_config.serializable(),
        }

class HashedBlock(Serializable):
    def __init__(self, block: Block, mining_entropy: bytes = b"") -> None:
        self.block = block
        self.block_hash = self.block.sha256()
        self.mining_entropy = mining_entropy
        self.mining_timestamp = Timestamp.now()

    def replace_mining_entropy(self, new_entropy: bytes) -> None:
        self.mining_entropy = new_entropy
        self.mining_timestamp = Timestamp.now()

    def mining_hash(self) -> bytes:
        v = self.block_hash + self.mining_entropy
        return hashlib.sha256(v).digest()

    def block_num(self) -> int:
        return self.block.block_num

    def hash_meets_difficulty(self) -> bool:
        h = self.mining_hash()
        zero_bytes = self.block.block_config.difficulty // 8
        zero_bits = self.block.block_config.difficulty - (zero_bytes * 8)
        one_bits = 8 - zero_bits

        for i in range(0, zero_bytes):
            if h[i] != 0:
                return False

        if h[zero_bytes] > 2**one_bits:
            return False
        else:
            return True

    def serializable(self) -> Ser:
        return {
            "block": self.block.serializable(),
            "mining_entropy": self.mining_entropy.hex(),
            "mined_hash": self.mining_hash().hex(),
            "mining_timestamp": self.mining_timestamp.serializable(),
        }
