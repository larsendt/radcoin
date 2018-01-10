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

def run_client_forever(cfg: Config) -> None:
    c = ChainClient(cfg)
    c.poll_forever()

@gen.coroutine
def start_client(cfg: Config):
    pool = ProcessPoolExecutor(max_workers=1)
    yield pool.submit(run_client_forever, cfg)

@gen.coroutine
def start_miner(cfg: Config):
    pool = ProcessPoolExecutor(max_workers=cfg.miner_procs())
    kp = KeyPair()
    yield [pool.submit(mine, kp, cfg) for i in range(cfg.miner_procs())]

def main():
    parser = argparse.ArgumentParser("Radcoin does stuff")
    parser.add_argument(
        "--initialize",
        help="Make new config. Will fail if config exists.",
        default=False,
        action="store_true")

    parser.add_argument(
        "--log_level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARN", "ERROR"])

    parser.add_argument(
        "--run_miner",
        help="If set, run a miner.",
        action="store_true",
        default=False)

    parser.add_argument(
        "--cfg_path",
        help="Path to the config file. If it doesn't exist, it will be created.",
        required=True)

    parser.add_argument(
        "--advertize_addr",
        help="The address to advertize to the network.",
        default=None)

    args = parser.parse_args()

    if args.initialize:
        ConfigBuilder.init_defaults(args.cfg_path)

    cfg: Config = ConfigBuilder(
        args.cfg_path,
        args.advertize_addr,
        args.log_level).build()

    print("Running server")
    serv = ChainServer(cfg)
    serv.listen()

    ioloop.IOLoop.current().spawn_callback(start_client, cfg)

    if args.run_miner:
        print("Running miner")
        ioloop.IOLoop.current().spawn_callback(start_miner, cfg)

    ioloop.IOLoop.current().start()

if __name__ == "__main__":
    main()
