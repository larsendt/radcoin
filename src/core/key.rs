use ring::{rand, signature};
use untrusted;

pub struct WalletPub {
    pub edd25519_pub_key: Vec<u8>,
}

pub struct WalletKeyPair {
    pub key_pair: signature::Ed25519KeyPair,
}

impl WalletKeyPair {
    pub fn new() -> Self {
		let rng = rand::SystemRandom::new();
		let pkcs8_bytes =
            signature::Ed25519KeyPair::generate_pkcs8(&rng).unwrap();

		let key_pair =
            signature::Ed25519KeyPair::from_pkcs8(
                untrusted::Input::from(&pkcs8_bytes))
            .unwrap();

        WalletKeyPair {
            key_pair: key_pair,
        }
    }

    pub fn public_key(&self) -> WalletPub {
        WalletPub {
            edd25519_pub_key: self.key_pair.public_key_bytes().to_vec(),
        }
    }
}
