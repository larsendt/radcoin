from core.block import HashedBlock
from core.chain import BlockChain
from core.config import Config
from core.dblog import DBLogger
from core.network import util
from core.network.peer_list import Peer, PeerList
from core.serializable import Hash
from core.storage.sqlite_chain import SqliteBlockChainStorage
from core.storage.sqlite_transaction import SqliteTransactionStorage
from core.transaction.signed_transaction import SignedTransaction
import json
from tornado import web
from typing import List

class DefaultRequestHandler(web.RequestHandler):
    def get(self) -> None:
        d = {
            "available_rpcs": [
                {"route": "/block",
                 "params": ["hex_hash", "parent_hex_hash", "block_num"],
                 "methods": ["get", "post"]},
                {"route": "/transaction", "methods": ["get", "post"]},
                {"route": "/peer", "methods": ["get", "post"]},
                {"route": "/chain", "methods": ["get"]},
            ]
        }
        self.write(d)

class BlockRequestHandler(web.RequestHandler):
    def initialize(
        self,
        chain: BlockChain,
        cfg: Config) -> None:

        self.chain = chain
        self.l = DBLogger(self, cfg)

    def get(self) -> None:
        requested_hash = self.get_query_argument("hex_hash", None)
        requested_block_num = self.get_query_argument("block_num", None)
        parent_hash = self.get_query_argument("parent_hex_hash", None)

        if requested_hash is not None:
            self.get_by_hash(Hash.fromhex(requested_hash))
        elif requested_block_num is not None:
            self.get_by_block_num(int(requested_block_num))
        elif parent_hash is not None:
            self.get_by_parent_hash(Hash.fromhex(parent_hash))
        else:
            self.set_status(400)
            self.write(util.error_response(
                "missing 'requested_hash' or 'requested_block_num' params"))

    def post(self) -> None:
        ser = self.request.body.decode('utf-8')
        hb = HashedBlock.deserialize(ser)

        if self.chain.storage.has_hash(hb.mining_hash()):
            self.set_status(200)
            self.write(util.generic_ok_response("already have that one"))
            return

        if not self.chain.storage.has_hash(hb.parent_mining_hash()):
            self.set_status(400)
            self.write(util.error_response("unknown parent"))
            return

        self.l.info("New block", hb.block_num(), hb.mining_hash())
        self.chain.add_block(hb)
        self.set_status(200)
        self.write(util.generic_ok_response())

    def get_by_hash(self, mining_hash: Hash) -> None:
        block = self.chain.storage.get_by_hash(mining_hash)

        if block:
            self.set_status(200)
            self.write(block.serializable())
        else:
            self.set_status(404)
            self.write(util.error_response("no block with given hash"))

    def get_by_block_num(self, block_num: int) -> None:
        blocks = self.chain.storage.get_by_block_num(block_num)
        ser_blocks = list(map(lambda b: b.serializable(), blocks))
        response = {"blocks": ser_blocks}
        self.set_status(200)
        self.write(response)

    def get_by_parent_hash(self, parent_mining_hash: Hash):
        blocks = self.chain.storage.get_by_parent_hash(parent_mining_hash)
        self.set_status(200)
        ser_blocks = list(map(lambda b: b.serializable(), blocks))
        resp = {"blocks": ser_blocks}
        self.write(resp)

class TransactionRequestHandler(web.RequestHandler):
    def initialize(self, cfg: Config, chain: BlockChain):
        self.l = DBLogger(self, cfg)
        self.chain = chain

    def get(self) -> None:
        txns = self.chain.transaction_storage.get_all_transactions()
        ser_txns = list(map(lambda t: t.serializable(), txns))
        resp = {"transactions": ser_txns}
        self.set_status(200)
        self.write(resp)

    def post(self) -> None:
        ser = self.request.body.decode('utf-8')
        txn = SignedTransaction.deserialize(ser)

        if self.chain.transaction_is_valid(txn):
            self.l.info("New transaction", txn)
            self.chain.add_transaction(txn)
            self.set_status(200)
            self.write(util.generic_ok_response())
        else:
            self.l.warn("Invalid transaction", txn)
            self.set_status(400)
            self.write(util.error_response("Invalid transaction"))

class PeerRequestHandler(web.RequestHandler):
    def initialize(self, peer_list: PeerList, cfg: Config) -> None:
        self.l = DBLogger(self, cfg)
        self.peer_list = peer_list
        self.cfg = cfg

    def get(self) -> None:
        peers = list(map(lambda p: p.serializable(),
                self.peer_list.get_all_active_peers()))
        resp = {
            "peers": peers,
            "peer_id": self.cfg.server_peer_id(),
        }
        self.set_status(200)
        self.write(resp)

    def post(self) -> None:
        peers = json.loads(self.request.body.decode('utf-8'))

        maybe_new_peers = list(map(lambda p: Peer(p["peer_id"], p["address"], p["port"]), peers["peers"]))
        new_peers: List[Peer] = []

        for peer in maybe_new_peers:
            if self.peer_list.has_peer(peer):
                self.l.info("Already have peer", peer)
                continue

            new_peers.append(peer)
            self.l.info("New peer", peer)
            self.peer_list.add_peer(peer)

        self.set_status(200)
        self.write(util.generic_ok_response())

class ChainRequestHandler(web.RequestHandler):
    def initialize(self, chain: BlockChain, cfg: Config):
        self.l = DBLogger(self, cfg)
        self.chain = chain

    def get(self) -> None:
        h = self.chain.get_head()
        resp = {
            "height": h.block_num(),
            "head_hash": h.mining_hash().serializable(),
        }
        self.set_status(200)
        self.write(resp)

class ChainServer(object):
    def __init__(self, cfg: Config) -> None:
        self.l = DBLogger(self, cfg)
        self.peer_list = PeerList(cfg)

        self.storage = SqliteBlockChainStorage(cfg)
        self.transaction_storage = SqliteTransactionStorage(cfg)
        self.chain = BlockChain(self.storage, self.transaction_storage, cfg)

        self.peer_info = Peer(
                cfg.server_peer_id(),
                cfg.server_advertize_addr(),
                cfg.server_listen_port())
        self.advertize_self = cfg.advertize_self()

        self.app = web.Application([
            web.url(r"/", DefaultRequestHandler),
            web.url(r"/block", BlockRequestHandler, {"chain": self.chain, "cfg": cfg}),
            web.url(r"/transaction", TransactionRequestHandler, {"chain": self.chain, "cfg": cfg}),
            web.url(r"/peer", PeerRequestHandler, {"peer_list": self.peer_list, "cfg": cfg}),
            web.url(r"/chain", ChainRequestHandler, {"cfg": cfg, "chain": self.chain}),
        ])

    def listen(self) -> None:
        if self.advertize_self:
            self.l.info("Advertizing self as peer")
            self.peer_list.add_peer(self.peer_info)
        else:
            self.l.info("Not advertizing self as peer")

        self.app.listen(self.peer_info.port, address="0.0.0.0")
