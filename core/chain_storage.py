from core.block import HashedBlock
from typing import List, Optional

class BlockChainStorage(object):
    def __init__(self):
        pass

    def add_block(self, block: HashedBlock) -> None:
        raise NotImplementedError()

    def get_by_hash(self, block_hash: bytes) -> HashedBlock:
        raise NotImplementedError()

    def get_height(self) -> int:
        raise NotImplementedError()

    def get_head(self) -> HashedBlock:
        raise NotImplementedError()

    def has_hash(self, block_hash: bytes) -> bool:
        raise NotImplementedError()

    def get_genesis(self) -> Optional[HashedBlock]:
        raise NotImplementedError()

    def get_by_parent_hash(self, parent_hash: bytes) -> List[HashedBlock]:
        raise NotImplementedError()

    def get_by_block_num(self, block_num: int) -> List[HashedBlock]:
        raise NotImplementedError()

    def get_range(self, start: int, stop: int) -> List[HashedBlock]:
        raise NotImplementedError()

    def get_all_non_genesis_in_order(self) -> List[HashedBlock]:
        raise NotImplementedError()
