from core.block import HashedBlock
from core.chain import BlockChain
from core.config import Config
from core.dblog import DBLogger
from core.network.peer_list import Peer, PeerList
from core.serializable import Hash
from core.storage.sqlite_chain import SqliteBlockChainStorage
from core.storage.sqlite_transaction import SqliteTransactionStorage
from core.transaction.signed_transaction import SignedTransaction
import json
import random
import requests
import time
from typing import Any, Dict, List, Optional, Set

class ChainClient(object):
    def __init__(self, cfg: Config) -> None:
        self.l = DBLogger(self, cfg)
        self.l.info("Init")
        self.peer_list = PeerList(cfg)
        self.self_peer = Peer(
                cfg.server_peer_id(),
                cfg.server_advertize_addr(),
                cfg.server_listen_port())

        self.chain = BlockChain(
            SqliteBlockChainStorage(cfg),
            SqliteTransactionStorage(cfg),
            cfg)
        self.cfg = cfg

    def poll_forever(self) -> None:
        while True:
            peers = self.our_peers()
            random.shuffle(peers)
            peer_sample = peers[:self.cfg.peer_sample_size()]
            for peer in peer_sample:
                self.l.debug("Syncing with peer", peer)
                self.sync(peer)
            time.sleep(self.cfg.poll_delay())

    def our_peers(self) -> List[Peer]:
        peers = self.peer_list.get_all_active_peers()
        peers = list(filter(lambda p: p != self.self_peer, peers))
        self.l.debug("Sampled peers", peers)
        return peers

    def sync(self, peer: Peer) -> None:
        peers = self.request_peers(peer)

        if peers is None:
            self.l.debug("Peer not responding", peer)
            return

        self.l.debug("Peer {} knows about {} peers".format(peer, len(peers)))

        for new_peer in peers:
            if not self.peer_list.has_peer(new_peer) and new_peer != self.self_peer:
                self.l.info("Peer {} previously unknown. Adding.".format(new_peer))
                self.peer_list.add_peer(new_peer)

        if self.cfg.advertize_self() and not self.self_peer in peers:
            self.l.info("Peer {} doesn't know about us, telling it.".format(peer))
            resp = self._peer_post(peer, "/peer", {"peers": [self.self_peer.serializable()]})
            if resp is None:
                self.l.info("Peer didn't respond", peer)

        transactions = self.request_transactions(peer)
        if transactions is None:
            self.l.info("Peer not responding", peer)
            return

        for txn in transactions:
            if not self.chain.transaction_storage.has_transaction(txn.signature):
                if self.chain.transaction_is_valid(txn):
                    self.l.info("New transaction", txn)
                    self.chain.add_outstanding_transaction(txn)
                else:
                    self.l.warn("Peer sent us an invalid transaction", peer, txn)

        peer_head = self.request_head(peer)
        if not peer_head:
            self.l.debug("Peer {} didn't give us a head block.".format(peer))
            return

        if self.chain.storage.has_hash(peer_head.mining_hash()):
            self.l.debug("Already have peer's head block")
            return

        if peer_head.block_num() == 0:
            self.l.warn("Peer returned a different genesis block than expected", peer, peer_head)
            return

        parent = self.request_block(peer_head.parent_mining_hash(), peer)

        if parent is None:
            self.l.debug("Wat. Peer didn't have parent:", peer_head.parent_mining_hash())
            return
            
        while not self.chain.storage.has_hash(parent.mining_hash()):
            parent = self.request_block(parent.parent_mining_hash(), peer)

            if parent is None:
                self.l.debug("Wat. Peer didn't have parent:", peer_head.parent_mining_hash())
                return

        to_request = [parent]
        while len(to_request) > 0:
            parent = to_request.pop(0)
            successors = self.request_successors(parent.mining_hash(), peer)

            if successors is None:
                self.l.debug("Peer is not responding", peer)
                return

            for succ in successors: # ( ͡° ͜ʖ ͡°)
                self.l.info("New block:", succ)
                to_request.append(succ)
                self.chain.add_block(succ)

    def request_block(self, block_hash: Hash, peer: Peer) -> Optional[HashedBlock]:
        obj = self._peer_get(peer, "/block", {"hex_hash": block_hash.hex()})
        if obj is None:
            self.l.debug("No HTTP response from peer {}".format(peer))
            return None

        if obj is None:
            self.l.debug("No block from peer", peer)
            return None

        try:
            hb = HashedBlock.from_dict(obj)
        except KeyError as e:
            self.l.debug("Invalid serialized block from peer {}".format(peer), exc=e)
            return None

        return hb

    def request_head(self, peer: Peer) -> Optional[HashedBlock]:
        head_hash = self.request_head_hash(peer)
        
        if head_hash is None:
            self.l.debug("Can't get head block from peer", peer)
            return None

        obj = self._peer_get(peer, "/block", {"hex_hash": head_hash.hex()})

        try:
            h = HashedBlock.from_dict(obj)
        except KeyError as e:
            self.l.debug("Invalid block from peer {}".format(peer), exc=e)
            return None

        return h

    def request_head_hash(self, peer: Peer) -> Optional[Hash]:
        obj = self._peer_get(peer, "/chain", {})

        if obj is None:
            self.l.debug("No head hash from peer", peer)
            return None

        try:
            h = Hash.from_dict(obj["head_hash"])
        except KeyError as e:
            self.l.debug("No head hash from peer {}".format(peer), exc=e)
            return None

        return h

    def request_successors(self, parent_hash: Hash, peer: Peer) -> Optional[List[HashedBlock]]:
        payload = {"parent_hex_hash": parent_hash.hex()}
        obj = self._peer_get(peer, "/block", payload)

        if obj is None:
            self.l.debug("No successors from peer", peer)
            return None

        if "blocks" not in obj:
            self.l.debug("Couldn't turn response into list of blocks", peer, obj)
            return None

        new_blocks: List[HashedBlock] = []
        for block_obj in obj["blocks"]:
            try:
                b = HashedBlock.from_dict(block_obj)
            except KeyError as e:
                self.l.debug("Invalid block object from peer", peer, obj)
                return None

            new_blocks.append(b)

        return new_blocks

    def request_peers(self, peer: Peer) -> Optional[List[Peer]]:
        obj = self._peer_get(peer, "/peer", {})
        if obj is None:
            self.l.debug("No peer response from peer", peer)
            return None

        if not "peers" in obj:
            self.l.debug("No peers in response from peer", peer, obj)
            return None

        new_peers: List[Peer] = []
        for peer_obj in obj["peers"]:
            try:
                new_peer = Peer.from_dict(peer_obj)
            except KeyError as e:
                self.l.debug("Invalid peer from peer", peer, new_peer)
                return []
            new_peers.append(new_peer)
        return new_peers

    def request_transactions(self, peer: Peer) -> Optional[List[SignedTransaction]]:
        obj = self._peer_get(peer, "/transaction", {})
        if obj is None:
            self.l.debug("No peer response from peer", peer)
            return None

        if not "transactions" in obj:
            self.l.debug("No transaction response from peer", peer, obj)
            return None

        new_transactions: List[SignedTransaction] = []
        for txn_obj in obj["transactions"]:
            try:
                new_txn = SignedTransaction.from_dict(txn_obj)
            except KeyError as e:
                self.l.debug("Invalid transaction from peer", peer, txn_obj, exc=e)
            else:
                new_transactions.append(new_txn)
        return new_transactions

    def _peer_get(
        self,
        peer: Peer,
        path: str,
        params: Dict[str, Any]) -> Optional[Dict[str, Any]]:

        url = peer.http_url(path)
        self.l.debug("get", url, params)

        try:
            r = requests.get(url, params=params)
            resp = r.content
        except requests.exceptions.ConnectionError as e:
            # todo: mark peer as inactive
            self.l.debug("No response from peer", peer, exc=e)
            return None

        try:
            obj = json.loads(resp)
        except ValueError as e:
            self.l.debug("Invalid JSON response from peer", peer, exc=e)
            return None

        return obj

    def _peer_post(
            self,
            peer: Peer,
            path: str,
            payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        url = peer.http_url(path)
        self.l.debug("post", url, payload)

        try:
            r = requests.post(url, json=payload)
            resp = r.content
        except requests.exceptions.ConnectionError as e:
            # todo: mark peer as inactive
            self.l.debug("No response from peer", peer, exc=e)
            return None

        try:
            obj = json.loads(resp)
        except ValueError as e:
            self.l.debug("Invalid JSON response from peer", peer, exc=e)
            return None

        return obj
