import argparse
from core.miner import BlockMiner
from core.key_pair import KeyPair
from core.network.client import ChainClient
from core.network.server import ChainServer
from concurrent.futures import ProcessPoolExecutor, wait
from tornado import ioloop, gen
import os
import traceback
from typing import Generator

def mine(key_pair: KeyPair) -> None:
    bm = BlockMiner()
    bm.mine_forever()

def client_poll() -> None:
    client = ChainClient()
    client.poll_forever()

@gen.coroutine
def start_miner():
    pool = ProcessPoolExecutor(max_workers=1)
    kp = KeyPair()
    yield pool.submit(mine, kp)

@gen.coroutine
def start_client():
    pool = ProcessPoolExecutor(max_workers=1)
    yield pool.submit(client_poll)

def start_server():
    serv = ChainServer()
    serv.listen(8888, address="0.0.0.0")

def mine_genesis():
    bm = BlockMiner() # pass in a key pair
    bm.mine_genesis()

def main():
    parser = argparse.ArgumentParser("Radcoin does stuff")
    parser.add_argument("--mine_genesis", default=False)
    parser.add_argument("--bootstrap", default=False)
    parser.add_argument("--server", default=False)
    parser.add_argument("--client", default=False)
    parser.add_argument("--miner", default=False)
    args = parser.parse_args()

    need_ioloop = False
    
    if args.mine_genesis:
        if args.bootstrap:
            print("--mine_genesis and --bootstrap are mutually exclusive")
        else:
            print("Mining genesis")
            mine_genesis()
    elif args.bootstrap:
        if args.mine_genesis:
            print("--mine_genesis and --bootstrap are mutually exclusive")
        else:
            print("Bootstrapping with temp client")
            c = ChainClient()
            c.bootstrap()

    if args.server:
        print("Running server")
        need_ioloop = True
        start_server()

    if args.client:
        print("Running client")
        need_ioloop = True
        ioloop.IOLoop.current().spawn_callback(start_client)

    if args.miner:
        print("Running miner")
        need_ioloop = True
        ioloop.IOLoop.current().spawn_callback(start_miner)

    if need_ioloop:
        ioloop.IOLoop.current().start()

if __name__ == "__main__":
    main()
