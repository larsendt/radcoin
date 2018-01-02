from core.block_config import BlockConfig
from core.key_pair import Address
from core.serializable import Hash, Serializable, Ser
from core.timestamp import Timestamp
from core.transaction.signed_transaction import SignedTransaction
import hashlib
from typing import List, Optional

class Block(Serializable):
    def __init__(
            self,
            block_num,
            parent_mining_hash: Optional[Hash],
            config: BlockConfig,
            transactions: List[SignedTransaction]) -> None:

        if parent_mining_hash is None:
            if block_num != 0:
                raise ValueError("Parent is none, but block num is > 0")
        else:
            if block_num == 0:
                raise ValueError("Parent is not None, but block num = 0")

        self.block_num = block_num
        self.block_config = config
        self.parent_mining_hash = parent_mining_hash
        self.transactions = transactions

    def __str__(self) -> str:
        return "Block<num={},parent={}>".format(
            self.block_num, self.parent_mining_hash)

    def serializable(self) -> Ser:
        txns = map(lambda t: t.serializable(), self.transactions)
        
        if self.parent_mining_hash is None:
            parent_hash = None
        else:
            parent_hash = self.parent_mining_hash.serializable()

        return {
            "block_num": self.block_num,
            "parent_mined_hash": parent_hash,
            "transactions": list(txns),
            "config": self.block_config.serializable(),
        }

    @staticmethod
    def from_dict(obj: Ser) -> 'Block':
        block_num = obj["block_num"]
        if obj["parent_mined_hash"] is not None:
            parent_hash = Hash.from_dict(obj["parent_mined_hash"])
        else:
            parent_hash = None
        txns = list(map(lambda o: SignedTransaction.from_dict(o), obj["transactions"]))
        config = BlockConfig.from_dict(obj["config"])
        return Block(block_num, parent_hash, config, txns)

class HashedBlock(Serializable):
    def __init__(
            self,
            block: Block,
            mining_entropy: bytes = b"",
            mining_timestamp: Optional[Timestamp] = None) -> None:
        self.block = block
        self.mining_entropy = mining_entropy
        if mining_timestamp is None:
            self.mining_timestamp = Timestamp.now()
        else:
            self.mining_timestamp = mining_timestamp

    def __str__(self) -> str:
        return "HashedBlock<num={},hash={}>".format(
            self.block_num(), self.mining_hash())

    def replace_mining_entropy(self, new_entropy: bytes) -> None:
        self.mining_entropy = new_entropy
        self.mining_timestamp = Timestamp.now()

    def mining_hash(self) -> Hash:
        v = self.block.sha256().raw_sha256 + self.mining_entropy
        return Hash(hashlib.sha256(v).digest())

    def parent_mining_hash(self) -> Hash:
        return self.block.parent_mining_hash

    def block_num(self) -> int:
        return self.block.block_num

    def hash_meets_difficulty(self) -> bool:
        h = self.mining_hash().raw_sha256
        zero_bytes = self.block.block_config.difficulty // 8
        zero_bits = self.block.block_config.difficulty - (zero_bytes * 8)
        one_bits = 8 - zero_bits

        for i in range(0, zero_bytes):
            if h[i] != 0:
                return False

        if h[zero_bytes] > ((2**one_bits) - 1):
            return False
        else:
            return True

    def serializable(self) -> Ser:
        return {
            "block": self.block.serializable(),
            "mining_entropy": self.mining_entropy.hex(),
            "mined_hash": self.mining_hash().serializable(),
            "mining_timestamp": self.mining_timestamp.serializable(),
        }

    @staticmethod
    def from_dict(obj: Ser) -> 'HashedBlock':
        block = Block.from_dict(obj["block"])
        mining_entropy = bytes.fromhex(obj["mining_entropy"])
        mining_timestamp = Timestamp.from_dict(obj["mining_timestamp"])
        hb = HashedBlock(
            block,
            mining_entropy=mining_entropy,
            mining_timestamp=mining_timestamp)
        return hb
