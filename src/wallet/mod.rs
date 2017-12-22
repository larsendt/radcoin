use core::amount::Amount;
use core::coin::Coin;
use core::key::{WalletKeyPair, WalletPub};
use core::transaction::{Transaction, SignedTransaction};

pub struct Wallet {
    key_pair: WalletKeyPair,
}

impl Wallet {
    pub fn new() -> Self {
        Wallet {
            key_pair: WalletKeyPair::new(),
        }
    }

    pub fn transaction_to(&self, to_addr: &WalletPub, coin: Coin, amount: Amount)
        -> SignedTransaction {
        let txn = Transaction::new(
            amount,
            coin,
            &self.address(),
            to_addr,
            0);

        txn.sign(&self.key_pair)
    }

    pub fn address(&self) -> WalletPub {
        self.key_pair.public_key()
    }
}
