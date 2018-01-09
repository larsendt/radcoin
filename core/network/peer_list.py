from core.config import Config
from core.dblog import DBLogger
from core.network import util
import random
import sqlite3
import time
import requests
from typing import List

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS peers (
    id INTEGER NOT NULL PRIMARY KEY,
    peer_id TEXT NOT NULL,
    address TEXT NOT NULL,
    port INTEGER NOT NULL,
    last_seen_unix_millis INTEGER NOT NULL,
    active INTEGER NOT NULL
)
"""

CREATE_PEER_ID_INDEX = """
CREATE UNIQUE INDEX IF NOT EXISTS peer_id_index ON peers(peer_id)
"""

HAS_PEER_SQL = "SELECT id FROM peers WHERE peer_id=?"
GET_ALL_ACTIVE_PEERS_SQL = "SELECT peer_id, address, port FROM peers WHERE active=1"

UPDATE_PEER_SQL = """
UPDATE peers
SET active=:active, last_seen_unix_millis=:last_seen_unix_millis, address=:address, port=:port
WHERE peer_id=:peer_id
"""

INSERT_PEER_SQL = """
INSERT INTO peers(peer_id, address, port, last_seen_unix_millis, active)
VALUES (:peer_id, :address, :port, :last_seen_unix_millis, :active)
"""

MARK_PEER_INACTIVE_SQL = "UPDATE peers SET active=0 WHERE peer_id=?"

class Peer(object):
    def __init__(self, peer_id: str, address: str, port: int) -> None:
        if len(peer_id) != util.PEER_ID_SIZE_BITS // 4:
            raise ValueError("Peer id must be 256 bits", peer_id)

        self.peer_id = peer_id
        self.address = address
        self.port = int(port)

    def is_ipv6(self):
        return ":" in self.address # HAX

    def http_url(self, path):
        if self.is_ipv6():
            ip = "[" + self.address + "]"
        else:
            ip = self.address

        if not path.startswith("/"):
            path = "/" + path
 
        return "http://" + ip + ":" + str(self.port) + path

    @staticmethod
    def request_id(address: str, port: int) -> 'Peer':
        tmp = Peer(util.generate_peer_id(), address, port)
        r = requests.get(tmp.http_url("/peer"))
        obj = r.json()
        peer_id = obj["peer_id"]
        return Peer(peer_id, address, port)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Peer):
            return self.peer_id == other.peer_id
        else:
            return False

    def __hash__(self) -> int:
        return hash(self.peer_id)

    def serializable(self):
        return {
            "peer_id": self.peer_id,
            "address": self.address,
            "port": self.port,
        }

    def __str__(self):
        return "Peer<{}>".format(self.peer_id)

    def __repr__(self):
        return self.__str__()

class PeerList(object):
    def __init__(self, cfg: Config) -> None:
        self.l = DBLogger(self, cfg)
        self._conn = sqlite3.connect(cfg.peer_db_path())

        self._conn.execute(CREATE_TABLE_SQL)
        self._conn.commit()

        self.gateway_peer = Peer.request_id(
            cfg.gateway_address(),
            cfg.gateway_port())

        self.self_peer = Peer(
            cfg.server_peer_id(),
            cfg.server_advertize_addr(),
            cfg.server_listen_port())

        self.add_peer(self.gateway_peer)

    def add_peer(self, peer: Peer) -> None:
        if peer == self.self_peer:
            self.l.debug("Not adding self peer")
            return
        elif self.has_peer(peer):
            self.l.debug("Update peer:", peer)
            self._update_peer(peer)
        else:
            self.l.debug("Insert peer:", peer)
            self._ins_peer(peer)

    def has_peer(self, peer: Peer) -> bool:
        args = {
            "address": peer.address,
            "port": peer.port,
        }

        c = self._conn.cursor()
        c.execute(HAS_PEER_SQL, args)
        return c.fetchone() is not None

    def mark_peer_inactive(self, peer: Peer) -> None:
        if peer == self.gateway_peer:
            self.l.warn("Not marking gateway as inactive")
            return
        elif not self.has_peer(peer):
            self.l.debug("Not marking unknown peer {} inactive".format(peer))
            return

        args = {
            "address": peer.address,
            "port": peer.port,
        }

        self._conn.execute(MARK_PEER_INACTIVE_SQL, args)
        self._conn.commit()

    def get_all_active_peers(self) -> List[Peer]:
        c = self._conn.cursor()
        c.execute(GET_ALL_ACTIVE_PEERS_SQL)
        return list(map(lambda row: Peer(*row), c))

    def random_peer(self) -> Peer:
        return random.choice(self.get_all_active_peers())

    def peer_sample(self, n: int) -> List[Peer]:
        return random.sample(self.get_all_active_peers(), n)

    def _update_peer(self, peer: Peer) -> None:
        args = {
            "last_seen_unix_millis": int(time.time() * 1000),
            "active": 1,
            "address": peer.address,
            "port": peer.port,
        }
        self._conn.execute(UPDATE_PEER_SQL, args)
        self._conn.commit()

    def _ins_peer(self, peer: Peer) -> None:
        args = {
            "last_seen_unix_millis": int(time.time() * 1000),
            "active": 1,
            "address": peer.address,
            "port": peer.port,
        }
        self._conn.execute(INSERT_PEER_SQL, args)
        self._conn.commit()
