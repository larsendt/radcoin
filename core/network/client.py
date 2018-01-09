from core.block import HashedBlock
from core.chain import BlockChain
from core.config import Config
from core.dblog import DBLogger
from core.network.peer_list import Peer, PeerList
from core.serializable import Hash
from core.sqlite_chain import SqliteBlockChainStorage
from core.transaction.signed_transaction import SignedTransaction
import json
import requests
import time
from typing import Any, Dict, List, Optional, Set

class ChainClient(object):
    def __init__(self, cfg: Config) -> None:
        self.l = DBLogger(self, cfg)
        self.l.info("Init")
        self.peer_list = PeerList(cfg)
        self.self_peer = Peer(cfg.server_advertize_addr(), cfg.server_listen_port())
        self.cfg = cfg

    def bootstrap(self) -> None:
        for peer in self.request_peers():
            if self.peer_list.has_peer(peer):
                self.l.info("Already have peer {}", peer)
                continue
            else:
                self.l.info("New peer {}", peer)
                self.peer_list.add_peer(peer)

        if self.cfg.advertize_self():
            self.l.info("Telling peers about self")
            self.transmit_peers([self.self_peer])
        else:
            self.l.info("Not telling peers about self")

        storage = SqliteBlockChainStorage(self.cfg)
        if not storage.get_genesis():
            self.l.info("Getting genesis block")
            genesis = self.request_genesis()
            storage.add_block(genesis)

        self.l.info("Init block chain")
        chain = BlockChain.load(storage, self.cfg)

        block = chain.get_head()
        self.l.info("Height is currently", block.block_num())

        while True:
            successors = self.request_successors(block.mining_hash())

            if len(successors) == 0:
                self.l.info("No more successors")
                break
            else:
                for block in successors:
                    self.l.info("New block {}", block.mining_hash())
                    chain.add_block(block)

        self.l.info("Finished bootstrapping")

    def add_local_peer(self, peer: Peer) -> None:
        self.peer_list.add_peer(peer)

    def request_successors(self, parent_hash: Hash) -> List[HashedBlock]:
        new_blocks: Set[HashedBlock] = set()

        for peer in self.get_peers():
            payload = {"parent_hex_hash": parent_hash.hex()}
            resp = self._peer_get(peer, "/block", payload)
            if resp is None:
                self.l.info("No response from", peer)
                continue

            obj = json.loads(resp)
            blocks = list(map(lambda b: HashedBlock.from_dict(b), obj["blocks"]))
            for block in blocks:
                new_blocks.add(block)

        return list(new_blocks)

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
            
            if not BlockChain.genesis_is_valid(block, self.l):
                self.l.warn("got an invalid genesis block from peer")
                continue

            return block

    def request_peers(self) -> List[Peer]:
        known_peers = self.get_peers()
        new_peers: Set[Peer] = set()
        for peer in known_peers:
            resp = self._peer_get(peer, "/peer", {}) 
            if resp:
                self.l.debug("Got peers from", peer)
                obj = json.loads(resp)
                ser_peers = obj["peers"]
                
                for ser in ser_peers:
                    new_peer = Peer(ser["address"], ser["port"])
                    new_peers.add(new_peer)

        self.l.info("Got {} new peers".format(len(new_peers)))
        return list(new_peers)

    def transmit_peers(self, new_peers: List[Peer]) -> None:
        all_peers = self.get_peers()
        payload = {"peers": list(map(lambda p: p.serializable(), new_peers))}
        print(payload)
        for peer in all_peers:
            self.l.info("Telling peer {} about peers".format(peer))
            self._peer_post(peer, "/peer", payload)

    def transmit_block(self, block: HashedBlock) -> None:
        self.l.info("Transmitting block {}".format(block.mining_hash()))
        for peer in self.get_peers():
            self.l.debug("transmitting {} to peer {}".format(
                block.mining_hash(), peer))
            payload = block.serializable()
            self._peer_post(peer, "/block", payload)

    def get_peers(self) -> List[Peer]:
        peers = self.peer_list.get_all_active_peers()
        peers = list(filter(lambda p: p == self.self_peer, peers))
        self.l.debug("Peers", peers)
        return peers

    def _peer_get(
        self,
        peer: Peer,
        path: str,
        params: Dict[Any, Any]) -> Optional[bytes]:

        url = peer.http_url(path)
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
        url = peer.http_url(path)
        self.l.debug("post", url, payload)

        try:
            r = requests.post(url, json=payload)
            self.l.debug(r.content)
        except requests.exceptions.ConnectionError as e:
            self.l.warn("No response from peer", peer)
            # todo: mark peer as inactive
            self.l.debug("Error from peer", peer, exc=e)
