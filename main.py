from core.miner import BlockMiner
from core.key_pair import KeyPair
from concurrent.futures import ProcessPoolExecutor, wait
from tornado import ioloop, gen
import os
import traceback
from typing import Generator

def mine(key_pair: KeyPair) -> None:
    bm = BlockMiner()
    bm.mine_forever()

@gen.coroutine
def async_mine(pool: ProcessPoolExecutor, key_pair: KeyPair) -> Generator:
    yield pool.submit(mine, key_pair)

@gen.coroutine
def main():
    pool = ProcessPoolExecutor(max_workers=4)
    kp = KeyPair()
    yield [async_mine(pool, kp), async_mine(pool, kp), async_mine(pool, kp), async_mine(pool, kp)]

if __name__ == "__main__":
    ioloop.IOLoop.current().run_sync(main)
