import argparse
from core.config import Config, ConfigBuilder
from core.miner import BlockMiner
from core.key_pair import KeyPair
from core.network.client import ChainClient
from core.network.peer_list import Peer
from core.network.server import ChainServer
from core.network import util
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

@gen.coroutine
def start_miner(cfg: Config):
    pool = ProcessPoolExecutor(max_workers=cfg.miner_procs())
    kp = KeyPair()
    yield [pool.submit(mine, kp, cfg) for i in range(cfg.miner_procs())]

def main():
    parser = argparse.ArgumentParser("Radcoin does stuff")
    parser.add_argument(
        "--mine_genesis",
        help="Mine a new genesis block. You probably generally don't want to do this.",
        default=False,
        action="store_true")

    parser.add_argument(
        "--cfg_path",
        help="Path to the config file. If it doesn't exist, it will be created.",
        required=True)

    parser.add_argument(
        "--advertize_addr",
        help="The address to advertize to the network.",
        default=None)

    args = parser.parse_args()

    cfg: Config = ConfigBuilder(args.cfg_path, args.advertize_addr).build()

    if args.mine_genesis:
        print("Mining genesis")
        bm = BlockMiner(cfg) # TODO: pass in a key pair
        bm.mine_genesis()

    print("Bootstrapping as necessary")
    client = ChainClient(cfg)
    client.bootstrap()

    print("Running server")
    serv = ChainServer(cfg)
    serv.listen()

    if args.run_miner:
        print("Running miner")
        ioloop.IOLoop.current().spawn_callback(start_miner, cfg)

    ioloop.IOLoop.current().start()

if __name__ == "__main__":
    main()
