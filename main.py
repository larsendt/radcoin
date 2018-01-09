import argparse
from core.config import Config
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
        "--log_level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARN", "ERROR"],
    )

    parser.add_argument(
        "--advertize_addr",
        help="Have the server advertize this address to the network.",
        default=None
    )

    parser.add_argument(
        "--listen_port",
        help="Listen on this port.",
        default="8989")

    parser.add_argument(
        "--no_advertize_self",
        help="If set, don't advertize ourselves as a peer.",
        action="store_false",
        default=True)

    parser.add_argument(
        "--run_miner",
        help="If set, run a miner.",
        action="store_true",
        default=False)

    parser.add_argument(
        "--miner_procs",
        help="Number miner of processes to run.",
        default=1)

    parser.add_argument(
        "--miner_throttle",
        help="Between 0 and 1. Fraction of the time that the miner should run.",
        default=1.0)

    args = parser.parse_args()

    print(args)

    if args.advertize_addr:
        advert_addr = args.advertize_addr
    else:
        advert_addr = util.resolve_external_address()

    print("Will advertize {} as our peer address".format(advert_addr))

    cfg = Config(
        args.log_level,
        advert_addr,
        args.listen_port,
        args.no_advertize_self,
        int(args.miner_procs),
        float(args.miner_throttle))

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
