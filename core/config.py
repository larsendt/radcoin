class Config(object):
    def __init__(
        self,
        log_level: str,
        advertize_addr: str,
        listen_port: int,
        advertize_self: bool,
        miner_procs: int,
        miner_throttle: float) -> None:

        self._log_level = log_level
        self._advertize_addr = advertize_addr
        self._listen_port = listen_port
        self._advertize_self = advertize_self
        self._miner_procs = miner_procs

        if 0 < miner_throttle <= 1:
            self._miner_throttle = miner_throttle
        else:
            raise ValueError("Miner throttle should be between 0 and 1")

    def log_level(self) -> str:
        return self._log_level

    def chain_db_path(self) -> str:
        return "chain.sqlite"

    def log_db_path(self) -> str:
        return "log.sqlite"

    def peer_db_path(self) -> str:
        return "peers.sqlite"

    def server_advertize_addr(self) -> str:
        return self._advertize_addr

    def server_listen_port(self) -> int:
        return self._listen_port

    def gateway_address(self) -> str:
        return "localhost"

    def gateway_port(self) -> int:
        return 8989

    def advertize_self(self) -> bool:
        return self._advertize_self

    def miner_procs(self) -> int:
        return self._miner_procs

    def miner_throttle(self) -> float:
        return self._miner_throttle
