from core.block import HashedBlock
from core.chain import BlockChain
from core.config import Config
from core.dblog import DBLogger
from core.network.peer_list import Peer, PeerList
from core.sqlite_chain import SqliteBlockChainStorage
from core.transaction import SignedTransaction
import json
import requests
import time
from typing import Any, Dict, Optional

class ChainClient(object):
    def __init__(self, cfg: Config) -> None:
        self.l = DBLogger(self, cfg)
        self.l.info("Init")
        self.peer_list = PeerList(cfg)
        self.storage = SqliteBlockChainStorage(cfg)
        self.chain: Optional[BlockChain] = None
        self.cfg = cfg

        if self.storage.get_genesis():
            self.chain = BlockChain.load(self.storage, cfg)
        else:
            self.l.warn("Storage has no genesis, either bootstrap via the client or mine a genesis block")

    def add_local_peer(self, peer: Peer) -> None:
        self.peer_list.add_peer(peer)

    def bootstrap(self) -> None:
        if self.storage.get_genesis():
            self.l.info("Already have genesis, no bootstrap needed")
            self.chain = BlockChain.load(self.storage, self.cfg)
        else:
            self.l.info("Requesting genesis block")
            genesis = self.request_genesis()
            self.chain = BlockChain.new(self.storage, genesis, self.cfg)
            self.l.info("Got genesis block")

    def request_genesis(self) -> HashedBlock:
        path = "/block"
        params = {"block_num": 0}

        while True:
            peer = self.peer_list.random_peer()
            resp_body = self._peer_get(peer, path, params)
            if resp_body:
                self.l.debug("resp body", resp_body)
            else:
                continue

            obj = json.loads(resp_body)
            block_obj = obj["blocks"][0]

            block = HashedBlock.from_dict(block_obj)
            if block.block_num() != 0:
                self.l.warn("got a non-genesis block from peer")
                continue
            
            if not block.is_valid():
                self.l.warn("got an invalid block from peer")
                continue

            return block

    def tell_peers(self) -> None:
        all_peers = self.peer_list.get_all_active_peers()
        payload = {"peers": list(map(lambda p: p.serializable(), all_peers))}
        for peer in all_peers:
            self.l.info("Telling peer {} about peers".format(peer))
            self._peer_post(peer, "/peer", payload)

    def poll_forever(self) -> None:
        while True:
            self.l.debug("Polling...")
            self.tell_peers()
            time.sleep(30) # half of a block

    def _peer_get(
        self,
        peer: Peer,
        path: str,
        params: Dict[Any, Any]) -> Optional[bytes]:

        url = "http://" + peer.address + ":" + str(peer.port) + path
        self.l.debug("get", url, params)

        try:
            r = requests.get(url, params=params)
            return r.content
        except requests.exceptions.ConnectionError as e:
            self.l.warn("No response from peer", peer)
            # todo: mark peer as inactive
            self.l.debug("Error from peer", peer, exc=e)
            return None

    def _peer_post(
            self,
            peer: Peer,
            path: str,
            payload: Any) -> None:
        url = "http://" + peer.address + ":" + str(peer.port) + path
        self.l.debug("post", url, payload)

        try:
            r = requests.post(url, json=payload)
            self.l.debug(r.content)
        except requests.exceptions.ConnectionError as e:
            self.l.warn("No response from peer", peer)
            # todo: mark peer as inactive
            self.l.debug("Error from peer", peer, exc=e)
