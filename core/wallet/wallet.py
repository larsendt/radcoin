from core.amount import Amount
from core.config import Config
from core.dblog import DBLogger
from core.key_pair import Address, KeyPair
from core.serializable import Serializable, Ser
from core.storage.sqlite_chain import SqliteBlockChainStorage
from core.storage.sqlite_transaction import SqliteTransactionStorage
from core.storage.sqlite_uxto import SqliteUXTOStorage
from core.storage.uxto_storage import UXTO
from core.transaction.signed_transaction import SignedTransaction
from nacl import pwhash, secret, utils
from typing import List

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS wallet (
    wallet_name TEXT NOT NULL,
    ed25519_pub_key BLOB NOT NULL,
    encryped_ed25519_seed BLOB NOT NULL
)"""

ADD_KEY_PAIR_SQL = """
INSERT INTO wallet VALUES (:name, :pub_key, :enc_priv_key)
"""

LIST_WALLETS_SQL = "SELECT DISTINCT(wallet_name) FROM wallet"

GET_KEY_PAIRS_FOR_WALLET = """
SELECT encrypted_ed25519_priv_key
FROM wallet
WHERE wallet_name = :wallet_name
"""

class Wallet(object):
    def __init__(self, cfg: Config, password: str) -> None:
        self.l = DBLogger(self, cfg)

        kdf = pwhash.argon2i.kdf
        salt = utils.random(pwhash.argon2i.SALTBYTES)
        ops = pwhash.argon2i.OPSLIMIT_SENSITIVE
        mem = pwhash.argon2i.MEMLIMIT_SENSITIVE

        self.l.info(
            "Deriving wallet encryption key, might take a couple seconds")
        self.key = kdf(secret.SecretBox.KEY_SIZE, password, salt,
                                 opslimit=ops, memlimit=mem)
        self.box = secret.SecretBox(Alices_key)

        self._uxto_storage = SqliteUXTOStorage(cfg)

        self._chain = BlockChain(
                SqliteBlockChainStorage(cfg),
                SqliteTransactionStorage(cfg),
                self._uxto_storage,
                cfg)

        self._conn = sqlite3.connect(cfg.wallet_path())
        self._conn.execute(CREATE_TABLE_SQL)
        self._conn.commit()

    def create_wallet(self, wallet_name: str) -> None:
        kp = KeyPair.new()
        self.add_existing_key_pair(wallet_name, kp)

    def add_existing_key_pair(
            self, wallet_name: str, key_pair: KeyPair) -> None:
        nonce = utils.random(secret.SecretBox.NONCE_SIZE)
        plaintext = bytes(key_pair._signing_key)
        encrypted = self.box.encrypt(plaintext, nonce)

        args = {
            "wallet_name": wallet_name,
            "ed25519_pub_key_hex": key_pair.address().hex(),
            "encrypted_ed25519_priv_key": encrypted,
        }

        self._conn.execute(ADD_KEY_PAIR_SQL, args)
        self._conn.commit()

    def list_wallets(self) -> List[str]:
        c = self._conn.cursor()
        c.execute(LIST_WALLETS_SQL)
        return map(lambda r: r[0], c)

    def get_balance(self, wallet_name: str) -> Amount:
        key_pairs = self.get_key_pairs(wallet_name)
        uxtos: List[UXTO] = []

        for kp in key_pairs:
            uxtos.extend(self._uxto_storage.unclaimed_outputs(kp.address()))
        return Amount.units(0)

    def create_transaction(
            self, wallet_name: str, to_addr: Address) -> None:
        pass

    def get_key_pairs(self, wallet_name: str) -> List[KeyPair]:
        args = {"wallet_name": wallet_name}
        c = self._conn.cursor()
        c.execute(GET_KEY_PAIRS_FOR_WALLET, args)
        return list(map(lambda row: KeyPair.from_seed(row[0]), c))
