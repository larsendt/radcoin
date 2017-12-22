use ring::signature;
use untrusted;

pub struct Signature {
    edd25519_sig: Vec<u8>,
}

impl Signature {
    pub fn from_edd25519_sig_bytes(msg: &[u8]) -> Self {
        Signature {
            edd25519_sig: msg.clone(),
        }
    }

    pub fn sign(key: &WalletKeyPair, msg: &[u8]) -> Self {
        let key_pair =
            signature::Ed25519KeyPair::from_pkcs8(
                untrusted::Input::from(&key.edd25519_pkcs8_keypair))?;

        let sig = key_pair.sign(msg);

        Signature {
            edd25519_sig: sig.as_ref().clone(),
        }
    }

    pub fn msg_has_valid_sig(&self, key: WalletPub, msg: &[u8]) -> bool {
        match signature::verify(
            &signature::ED25519, peer_public_key, msg, sig) {
            Ok(_) => true,
            Err(_) => false,
        }
    }
}
