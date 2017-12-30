from core.amount import Amount
from core.coin import Coin
from core.key_pair import KeyPair
from core.transaction import Transaction, SignedTransaction

me = KeyPair()
somebody = KeyPair()

t = Transaction(Amount.units(1, Coin.Radcoin))
t.addresses(me.address(), somebody.address())
s = SignedTransaction.sign(t, me)

print(s.serializable())
print(s.is_valid())
