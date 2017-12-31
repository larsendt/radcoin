from core.block import HashedBlock
from core.chain import BlockChain
from core.config import DB_PATH, LOG_PATH
from core.dblog import DBLogger
from core.network import util
from core.network.peer_list import Peer, PeerList
from core.sqlite_chain import SqliteBlockChainStorage
from core.transaction import SignedTransaction
import json
from tornado import web

class DefaultRequestHandler(web.RequestHandler):
    def get(self) -> None:
        d = {
            "available_rpcs": [
                {"route": "/block", "params": ["hex_hash", "block_num"], "methods": ["get", "post"]},
                {"route": "/transaction", "methods": ["get", "post"]},
                {"route": "/peer", "methods": ["get", "post"]},
            ]
        }
        self.write(d)

class BlockRequestHandler(web.RequestHandler):
    def initialize(self, chain: BlockChain) -> None:
        self.chain = chain
        self.l = DBLogger(self, LOG_PATH)

    def get(self) -> None:
        requested_hash = self.get_query_argument("hex_hash", None)
        requested_block_num = self.get_query_argument("block_num", None)

        if requested_hash is not None:
            self.get_by_hash(bytes.fromhex(requested_hash))
        elif requested_block_num is not None:
            self.get_by_block_num(int(requested_block_num))
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

        self.chain.add_block(hb)
        self.set_status(200)
        self.write(util.generic_ok_response())

    def get_by_hash(self, mining_hash: bytes) -> None:
        block = self.chain.storage.get_by_hash(mining_hash)

        if block:
            self.set_status(200)
            self.write(block.serializable())
        else:
            self.set_status(400)
            self.write(util.error_response("no block with given hash"))

    def get_by_block_num(self, block_num: int) -> None:
        blocks = self.chain.storage.get_by_block_num(block_num)
        ser_blocks = list(map(lambda b: b.serializable(), blocks))
        response = {"blocks": ser_blocks}
        self.set_status(200)
        self.write(response)

class TransactionRequestHandler(web.RequestHandler):
    def initialize(self):
        self.l = DBLogger(self, LOG_PATH)

    def get(self) -> None:
        self.write(util.error_response("unimplemented"))

    def post(self) -> None:
        self.write(util.error_response("unimplemented"))

class PeerRequestHandler(web.RequestHandler):
    def initialize(self, peer_list):
        self.l = DBLogger(self, LOG_PATH)
        self.peer_list = peer_list

    def get(self) -> None:
        peers = list(map(lambda p: p.serializable(),
                self.peer_list.get_all_active_peers()))
        resp = {"peers": peers}
        self.set_status(200)
        self.write(resp)

    def post(self) -> None:
        peers = json.loads(self.request.body.decode('utf-8'))

        for peer in peers["peers"]:
            p = Peer(peer["address"], peer["port"])
            self.peer_list.add_peer(p)

        self.set_status(200)
        self.write(util.generic_ok_response())

class ChainServer(object):
    def __init__(self) -> None:
        self.l = DBLogger(self, LOG_PATH)
        self.peer_list = PeerList()
        self.storage = SqliteBlockChainStorage(DB_PATH)

        if self.storage.get_genesis() is None:
            raise Exception(
                "Can't start server without a genesis block in the chain storage.")

        self.l.info("Loading existing chain")
        self.chain = BlockChain.load(self.storage)

        self.app = web.Application([
            web.url(r"/", DefaultRequestHandler),
            web.url(r"/block", BlockRequestHandler, {"chain": self.chain}),
            web.url(r"/transaction", TransactionRequestHandler),
            web.url(r"/peer", PeerRequestHandler, {"peer_list": self.peer_list}),
        ])

    def listen(self, port: int, address="") -> None:
        self.peer_list.add_peer(Peer(address, port))
        self.app.listen(port, address=address)
