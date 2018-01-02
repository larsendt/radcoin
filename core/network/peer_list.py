from core.config import Config
from core.dblog import DBLogger
import random
import sqlite3
import time
from typing import List

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS peers (
    id INTEGER NOT NULL PRIMARY KEY,
    address TEXT NOT NULL,
    port INTEGER NOT NULL,
    last_seen_unix_millis INTEGER NOT NULL,
    active INTEGER NOT NULL
)
"""

CREATE_IP_PORT_INDEX = """
CREATE UNIQUE INDEX IF NOT EXISTS ip_port_index ON peers(address, port)
"""

HAS_PEER_SQL = "SELECT id FROM peers WHERE address=:address AND port=:port"
GET_ALL_ACTIVE_PEERS_SQL = "SELECT address, port FROM peers WHERE active=1"

UPDATE_PEER_SQL = """
UPDATE peers SET active=:active, last_seen_unix_millis=:last_seen_unix_millis
WHERE address=:address AND port=:port
"""

INSERT_PEER_SQL = """
INSERT INTO peers(address, port, last_seen_unix_millis, active)
VALUES (:address, :port, :last_seen_unix_millis, :active)
"""

MARK_PEER_INACTIVE_SQL = """
UPDATE peers SET active=0 WHERE address=:address AND port=:port
"""

GATEWAY_ADDRESS = "radcoin.larsendt.com"
GATEWAY_PORT = 8888

class Peer(object):
    def __init__(self, address: str, port: int) -> None:
        self.address = address
        self.port = port

    def serializable(self):
        return {
            "address": self.address,
            "port": self.port,
        }

    def __str__(self):
        return "Peer<{}:{}>".format(self.address, self.port)

    def __repr__(self):
        return self.__str__()

class PeerList(object):
    def __init__(self, cfg: Config) -> None:
        self.l = DBLogger(self, cfg)
        self._conn = sqlite3.connect(cfg.peer_db_path())

        self._conn.execute(CREATE_TABLE_SQL)
        self._conn.commit()

        self.add_peer(Peer(GATEWAY_ADDRESS, GATEWAY_PORT))

    def add_peer(self, peer: Peer) -> None:
        if self.has_peer(peer):
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
        if not self.has_peer(peer):
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
