pub struct Transaction {
    pub amount_micros: u64,
    pub coin: Coin
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
        amount_micros: u64,
        coin: Coin,
        from: WalletPub,
        to: WalletPub,
        timestamp_millis: i64)
        -> Self {

        Transaction {
            amount_micros: amount_micros,
            coin: coin,
            from: WalletPub,
            to: WalletPub,
            timestamp_millis: timestamp_millis,
        }
    }

    pub fn sign(self, key: WalletKeyPair) -> SignedTransaction {
        let sig = Signature::sign(&key, &(self.bytes_for_signing()));
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
        match Signature::verify(
            self.transaction.from_addr,
            self.signature,
            self.transaction.bytes_for_signing()) {
            Signature::Valid => true,
            Signature::Invalid => false,
            e => panic!("Unexpected signature verification status {:?}", e),
        }
    }

    pub fn serialized_for_block(&self) -> Vec<u8> {
        vec![1, 2, 3, 4]
    }
}
