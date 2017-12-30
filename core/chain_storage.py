from core.block import HashedBlock
from typing import Iterator, Optional

class BlockChainStorage(object):
    def __init__(self):
        pass

    def add_block(self, block: HashedBlock) -> None:
        raise NotImplementedError()

    def get_by_hash(self, block_hash: bytes) -> HashedBlock:
        raise NotImplementedError()

    def has_hash(self, block_hash: bytes) -> bool:
        raise NotImplementedError()

    def get_genesis(self) -> Optional[HashedBlock]:
        raise NotImplementedError()

    def get_by_parent_hash(self, parent_hash: bytes) -> Iterator[HashedBlock]:
        raise NotImplementedError()

    def get_by_block_num(self, block_num: int) -> Iterator[HashedBlock]:
        raise NotImplementedError()

    def get_range(self, start: int, stop: int) -> Iterator[HashedBlock]:
        raise NotImplementedError()

    def get_all_in_order(self) -> Iterator[HashedBlock]:
        raise NotImplementedError()
