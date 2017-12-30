from core.amount import Amount
from core.block import Block, HashedBlock
from core.coin import Coin
from core.key_pair import KeyPair
from core.transaction import Transaction, SignedTransaction
import os

me = KeyPair()
somebody = KeyPair()

t = Transaction(Amount.units(1, Coin.Radcoin))
t.addresses(me.address(), somebody.address())
s = SignedTransaction.sign(t, me)

b = Block(0, me.address(), [s])
hb = HashedBlock(b, os.urandom(32))

print(hb.serialize())
