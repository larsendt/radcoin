class Config(object):
    def __init__(
        self,
        log_level: str,
        listen_addr: str,
        listen_port: int,
        advertize_self: bool) -> None:
        self._log_level = log_level
        self._listen_addr = listen_addr
        self._listen_port = listen_port
        self._advertize_self = advertize_self

    def log_level(self) -> str:
        return self._log_level

    def chain_db_path(self) -> str:
        return "chain.sqlite"

    def log_db_path(self) -> str:
        return "log.sqlite"

    def peer_db_path(self) -> str:
        return "peers.sqlite"

    def server_listen_addr(self) -> str:
        return self._listen_addr

    def server_listen_port(self) -> int:
        return self._listen_port

    def gateway_address(self) -> str:
        return "radcoin.larsendt.com"

    def gateway_port(self) -> int:
        return 8989

    def advertize_self(self) -> bool:
        return self._advertize_self
