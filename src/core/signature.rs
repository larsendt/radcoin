use ring::signature;
use super::key::{WalletKeyPair, WalletPub};
use untrusted;

#[derive(Deserialize, Serialize)]
pub struct Signature {
    edd25519_sig: Vec<u8>,
}

impl Signature {
    pub fn sign(key: &WalletKeyPair, msg: &[u8]) -> Self {
        let sig = key.key_pair.sign(msg);

        Signature {
            edd25519_sig: sig.as_ref().to_vec()
        }
    }

    pub fn msg_has_valid_sig(&self, key: &WalletPub, msg: &[u8]) -> bool {
        let msg_input = untrusted::Input::from(msg);
        let key_input = untrusted::Input::from(&key.edd25519_pub_key);
        let sig_input = untrusted::Input::from(&self.edd25519_sig);

        match signature::verify(
            &signature::ED25519, key_input, msg_input, sig_input) {
            Ok(_) => true,
            Err(_) => false,
        }
    }
}
