use super::amount::Amount;
use super::coin::Coin;
use super::key::{WalletKeyPair, WalletPub};
use super::signature::Signature;
use serde_json;

#[derive(Deserialize, Serialize)]
pub struct Transaction {
    pub amount: Amount,
    pub coin: Coin,
    pub from_addr: WalletPub,
    pub to_addr: WalletPub,
    pub timestamp_millis: i64,
}

#[derive(Deserialize, Serialize)]
pub struct SignedTransaction {
    pub transaction: Transaction,
    pub signature: Signature,
}

impl Transaction {
    pub fn new(
        amount: Amount,
        coin: Coin,
        from_addr: WalletPub,
        to_addr: WalletPub,
        timestamp_millis: i64)
        -> Self {

        Transaction {
            amount: amount,
            coin: coin,
            from_addr: from_addr,
            to_addr: to_addr,
            timestamp_millis: timestamp_millis,
        }
    }

    pub fn serialized_for_signing(&self) -> Vec<u8> {
        serde_json::to_vec(self).unwrap()
    }
}

impl SignedTransaction {
    pub fn sign(transaction: Transaction, from_keypair: &WalletKeyPair)
        -> Self {

        let sig = Signature::sign(
            from_keypair,
            &(transaction.serialized_for_signing()));

        SignedTransaction {
            transaction: transaction,
            signature: sig,
        }
    }

    pub fn signature_is_valid(&self) -> bool {
        self.signature.msg_has_valid_sig(
            &self.transaction.from_addr,
            &self.transaction.serialized_for_signing())
    }

    pub fn serialized_for_block(&self) -> Vec<u8> {
        serde_json::to_vec(self).unwrap()
    }
}

#[cfg(test)]
mod tests {
    use core::amount::Amount;
    use core::coin::Coin;
    use core::key::{WalletKeyPair, WalletPub};
    use core::transaction::{Transaction, SignedTransaction};

    #[test]
    fn test_valid_transaction_is_valid() {
        let me = WalletKeyPair::new();
        let somebody = WalletKeyPair::new();

        let txn = Transaction::new(
            Amount::units(1),
            Coin::Radcoin,
            me.public_key(),
            somebody.public_key(),
            0);

        let signed = SignedTransaction::sign(txn, &me);

        assert_eq!(signed.signature_is_valid(), true);
    }

    #[test]
    fn test_transaction_with_sender_signer_mismatch_is_invalid() {
        let me = WalletKeyPair::new();
        let somebody = WalletKeyPair::new();
        let third_person = WalletKeyPair::new();

        let txn = Transaction::new(
            Amount::units(1),
            Coin::Radcoin,
            third_person.public_key(),
            somebody.public_key(),
            0);

        let signed = SignedTransaction::sign(txn, &me);

        assert_eq!(signed.signature_is_valid(), false);
    }
}
