import json
import os
from typing import Any, Dict, Optional
from core.network import util
from core.peer import generate_peer_id

DEFAULTS = {
    "chain_db_path": "./chain.sqlite",
    "log_db_path": "./log.sqlite",
    "peer_db_path": "./peers.sqlite",
    "gateway_address": "radcoin.larsendt.com",
    "gateway_port": 8989,
    "miner_procs": 1, # number of processes to run
    "miner_throttle": 1.0, # attempt to use no more than this fraction of each CPU
    "advertize_self": True, # set this to false if you can't run a server
    "listen_port": 8989,
    "log_level": "INFO", # see core.dblog
    "peer_sample_size": 10, # when choosing a random set of peers, use this many
    "poll_delay": 5 # seconds
}

class Config(object):
    def __init__(self, args: Dict[Any, Any]) -> None:

        self._log_level = args["log_level"]
        self._advertize_addr = args["advertize_addr"]
        self._listen_port = int(args["listen_port"])
        self._server_peer_id = args["peer_id"]
        self._advertize_self = args["advertize_self"]
        self._miner_procs = int(args["miner_procs"])
        self._chain_db_path = args["chain_db_path"]
        self._log_db_path = args["log_db_path"]
        self._peer_db_path = args["peer_db_path"]
        self._gateway_address = args["gateway_address"]
        self._gateway_port = int(args["gateway_port"])
        self._peer_sample_size = int(args["peer_sample_size"])
        self._poll_delay = int(args["poll_delay"])

        if 0 < args["miner_throttle"] <= 1:
            self._miner_throttle = args["miner_throttle"]
        else:
            raise ValueError("Miner throttle should be between 0 and 1")

    def log_level(self) -> str:
        return self._log_level

    def chain_db_path(self) -> str:
        return self._chain_db_path

    def log_db_path(self) -> str:
        return self._log_db_path

    def peer_db_path(self) -> str:
        return self._peer_db_path

    def server_advertize_addr(self) -> str:
        return self._advertize_addr

    def server_listen_port(self) -> int:
        return self._listen_port

    def server_peer_id(self) -> str:
        return self._server_peer_id

    def gateway_address(self) -> str:
        return self._gateway_address

    def gateway_port(self) -> int:
        return self._gateway_port

    def advertize_self(self) -> bool:
        return self._advertize_self

    def miner_procs(self) -> int:
        return self._miner_procs

    def miner_throttle(self) -> float:
        return self._miner_throttle

    def peer_sample_size(self) -> int:
        return self._peer_sample_size

    def poll_delay(self) -> int:
        return self._poll_delay

class ConfigBuilder(object):
    def __init__(self,
        cfg_path,
        advertize_addr: Optional[str] = None,
        log_level: Optional[str] = None) -> None:

        self.cfg = DEFAULTS

        if os.path.exists(cfg_path):
            with open(cfg_path, "r") as f:
                for key, value in json.load(f).items():
                    self.cfg[key] = value

        if "peer_id" not in self.cfg:
            self.cfg["peer_id"] = generate_peer_id()

        if advertize_addr:
            self.cfg["advertize_addr"] = advertize_addr
        else:
            self.cfg["advertize_addr"] = util.resolve_external_address()

        if log_level is not None:
            self.cfg["log_level"] = log_level

        print("Saving config")
        with open(cfg_path, "w") as f:
            json.dump(self.cfg, f, indent=2)

    def build(self) -> Config:
        print("Building config", self.cfg)
        return Config(self.cfg)
