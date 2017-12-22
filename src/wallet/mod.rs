use core::key::{WalletKeyPair, WalletPub};

pub struct Wallet {
    pub key_pair: WalletKeyPair,
}

impl Wallet {
    pub fn new() -> Self {
        Wallet {
            key_pair: WalletKeyPair::new(),
        }
    }

    pub fn address(&self) -> WalletPub {
        self.key_pair.public_key()
    }
}
