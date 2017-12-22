use super::amount::Amount;
use super::coin::Coin;
use super::key::{WalletKeyPair, WalletPub};
use super::signature::Signature;

pub struct Transaction<'a> {
    pub amount: Amount,
    pub coin: Coin,
    pub from_keypair: &'a WalletKeyPair,
    pub to_addr: &'a WalletPub,
    pub timestamp_millis: i64,
}

pub struct SignedTransaction<'a> {
    pub transaction: Transaction<'a>,
    pub signature: Signature,
}

impl<'a> Transaction<'a> {
    pub fn new(
        amount: Amount,
        coin: Coin,
        from: &'a WalletKeyPair,
        to: &'a WalletPub,
        timestamp_millis: i64)
        -> Self {

        Transaction {
            amount: amount,
            coin: coin,
            from_keypair: from,
            to_addr: to,
            timestamp_millis: timestamp_millis,
        }
    }

    pub fn serialized_for_signing(&self) -> Vec<u8> {
        let a = self.amount.serialize();
        let c = self.coin.serialize();
        let f = self.from_keypair.public_key().serialize();
        let t = self.to_addr.serialize();
        let ts = format!("{}_unix_millis", self.timestamp_millis);
        let fmt = format!(
            "amount:{},coin:{},from:{},to:{},timestamp:{}",
            a, c, f, t, ts);
        println!("{}", fmt);
        fmt.into_bytes()
    }
}

impl<'a> SignedTransaction<'a> {
    pub fn sign(transaction: Transaction<'a>) -> Self {
        let sig = Signature::sign(
            &transaction.from_keypair,
            &(transaction.serialized_for_signing()));

        SignedTransaction {
            transaction: transaction,
            signature: sig,
        }
    }

    pub fn signature_is_valid(&self) -> bool {
        self.signature.msg_has_valid_sig(
            &self.transaction.from_keypair.public_key(),
            &self.transaction.serialized_for_signing())
    }

    pub fn serialized_for_block(&self) -> Vec<u8> {
        vec![1, 2, 3, 4]
    }
}
