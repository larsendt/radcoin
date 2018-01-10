from core.serializable import Serializable, Ser
import ipaddress
import os
import requests

PEER_ID_SIZE_BITS = 256

def generate_peer_id() -> str:
    return os.urandom(PEER_ID_SIZE_BITS // 8).hex()

def is_ipv6(address: str) -> bool:
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        return False # assume it's a domain

    return isinstance(ip, ipaddress.IPv6Address)

def http_url(address: str, port: int, path: str) -> str:
    if is_ipv6(address):
        ip = "[" + address + "]"
    else:
        ip = address

    if not path.startswith("/"):
        path = "/" + path

    return "http://" + ip + ":" + str(port) + path

class Peer(Serializable):
    def __init__(self, peer_id: str, address: str, port: int) -> None:
        if len(peer_id) != PEER_ID_SIZE_BITS // 4:
            raise ValueError("Peer id must be 256 bits", peer_id)

        self.peer_id = peer_id
        self.address = address
        self.port = int(port)

    def is_ipv6(self):
        return is_ipv6(self.address)

    def http_url(self, path):
        return http_url(self.address, self.port, path)

    @staticmethod
    def request_id(address: str, port: int) -> str:
        tmp = Peer(generate_peer_id(), address, port)
        r = requests.get(tmp.http_url("/peer"))
        obj = r.json()
        return obj["peer_id"]

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Peer):
            return self.peer_id == other.peer_id
        else:
            return False

    def __hash__(self) -> int:
        return hash(self.peer_id)

    def __str__(self):
        return "Peer<{}>".format(self.peer_id)

    def __repr__(self):
        return self.__str__()

    def serializable(self) -> Ser:
        return {
            "peer_id": self.peer_id,
            "address": self.address,
            "port": self.port,
        }

    @staticmethod
    def from_dict(obj: Ser) -> 'Peer':
        return Peer(obj["peer_id"], obj["address"], obj["port"])

