use super::amount::Amount;
use super::coin::Coin;
use super::key::{WalletKeyPair, WalletPub};
use super::signature::Signature;

pub struct Transaction {
    pub amount: Amount,
    pub coin: Coin,
    pub from_addr: WalletPub,
    pub to_addr: WalletPub,
    pub timestamp_millis: i64,
}

pub struct SignedTransaction {
    pub transaction: Transaction,
    pub signature: Signature,
}

impl Transaction {
    pub fn new(
        amount: Amount,
        coin: Coin,
        from: &WalletPub,
        to: &WalletPub,
        timestamp_millis: i64)
        -> Self {

        Transaction {
            amount: amount,
            coin: coin,
            from_addr: *from,
            to_addr: *to,
            timestamp_millis: timestamp_millis,
        }
    }

    pub fn sign(self, key: &WalletKeyPair) -> SignedTransaction {
        let sig = Signature::sign(&key, &(self.serialized_for_signing()));
        SignedTransaction::new(self, sig)
    }

    pub fn serialized_for_signing(&self) -> Vec<u8> {
        vec![1, 2, 3, 4]
    }
}

impl SignedTransaction {
    pub fn new(transaction: Transaction, signature: Signature) -> Self {
        SignedTransaction {
            transaction: transaction,
            signature: signature,
        }
    }

    pub fn signature_is_valid(&self) -> bool {
        self.signature.msg_has_valid_sig(
            self.transaction.from_addr,
            &self.transaction.serialized_for_signing())
    }

    pub fn serialized_for_block(&self) -> Vec<u8> {
        vec![1, 2, 3, 4]
    }
}
