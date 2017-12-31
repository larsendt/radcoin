from core.block import HashedBlock
from core.chain import BlockChain
from core.config import DB_PATH, LOG_PATH
from core.dblog import DBLogger
from core.network.peer_list import Peer, PeerList
from core.sqlite_chain import SqliteBlockChainStorage
from core.transaction import SignedTransaction
import requests
import time
from typing import Optional

class ChainClient(object):
    def __init__(self) -> None:
        self.l = DBLogger(self, LOG_PATH)
        self.l.info("Init")
        self.peer_list = PeerList()
        self.storage = SqliteBlockChainStorage(DB_PATH)
        self.chain: Optional[BlockChain] = None

        if self.storage.get_genesis():
            self.chain = BlockChain.load(self.storage)
        else:
            self.l.warn("Storage has no genesis, either bootstrap via the client or mine a genesis block")

    def bootstrap(self) -> None:
        if self.storage.get_genesis():
            self.l.info("Already have genesis, no bootstrap needed")
            self.chain = BlockChain.load(self.storage)
        else:
            self.l.info("Requesting genesis block")
            genesis = self.request_genesis()
            self.chain = BlockChain.new(self.storage, genesis)
            self.l.info("Got genesis block")

    def request_genesis(self) -> HashedBlock:
        path = "/block"
        params = {"block_num": 0}

        while True:
            resp_body = self._random_peer_get(path, params)
            if not resp_body:
                self.l.warn("no response from peer")
                continue

            block = HashedBlock.deserialize(resp_body)
            if block.block_num() != 0:
                self.l.warn("got a non-genesis block from peer")
                continue
            
            if not block.is_valid():
                self.l.warn("got an invalid block from peer")
                continue

            return block

    def poll_forever(self) -> None:
        while True:
            self.l.debug("Polling...")
            time.sleep(1)

    def _random_peer_get(self, path, params) -> Optional[bytes]:
        peer = self.peer_list.random_peer()
        url = "http://" + peer.address + ":" + str(peer.port) + path
        self.l.info("get", url, params)

        try:
            r = requests.get(url, data=params)
            return r.content
        except requests.exceptions.ConnectionError as e:
            self.l.debug("Error from peer", peer, exc=e)
            return None

