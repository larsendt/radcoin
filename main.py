import argparse
from core.config import Config
from core.miner import BlockMiner
from core.key_pair import KeyPair
from core.network.client import ChainClient
from core.network.peer_list import Peer
from core.network.server import ChainServer
from concurrent.futures import ProcessPoolExecutor, wait
from tornado import ioloop, gen
import os
import traceback
from typing import Generator

SERVER_ADDRESS="0.0.0.0"
SERVER_PORT=8888

def mine(key_pair: KeyPair, cfg: Config) -> None:
    bm = BlockMiner(cfg)
    bm.mine_forever()

def client_poll(cfg: Config) -> None:
    client = ChainClient(cfg)
    client.poll_forever()

@gen.coroutine
def start_miner(cfg: Config):
    pool = ProcessPoolExecutor(max_workers=1)
    kp = KeyPair()
    yield pool.submit(mine, kp, cfg)

@gen.coroutine
def start_client(cfg: Config):
    pool = ProcessPoolExecutor(max_workers=1)
    yield pool.submit(client_poll, cfg)

def main():
    parser = argparse.ArgumentParser("Radcoin does stuff")
    parser.add_argument(
        "--mine_genesis",
        help="Mine a new genesis block. You probably generally don't want to do this.",
        default=False,
        action="store_true")

    parser.add_argument(
        "--bootstrap",
        help="Request the genesis block from the network.",
        default=False,
        action="store_true")

    parser.add_argument(
        "--log_level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARN", "ERROR"],
    )

    parser.add_argument(
        "--listen_addr",
        help="Have the server listen on this addr and advertize it to the network.",
        required=True)

    parser.add_argument(
        "--no_advertize_self",
        help="If set, don't advertize ourselves as a peer.",
        action="store_false",
        default=True)

    args = parser.parse_args()

    print(args)

    cfg = Config(args.log_level, args.listen_addr, args.no_advertize_self)

    if args.mine_genesis:
        if args.bootstrap:
            print("--mine_genesis and --bootstrap are mutually exclusive")
        else:
            print("Mining genesis")
            bm = BlockMiner(cfg) # TODO: pass in a key pair
            bm.mine_genesis()
    elif args.bootstrap:
        if args.mine_genesis:
            print("--mine_genesis and --bootstrap are mutually exclusive")
        else:
            print("Bootstrapping with temp client")
            c = ChainClient(cfg)
            c.bootstrap()

    print("Running server")
    serv = ChainServer(cfg)
    serv.listen()

    print("Running client")
    ioloop.IOLoop.current().spawn_callback(start_client, cfg)

    print("Running miner")
    ioloop.IOLoop.current().spawn_callback(start_miner, cfg)

    ioloop.IOLoop.current().start()

if __name__ == "__main__":
    main()
