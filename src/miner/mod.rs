use core::amount::Amount;
use core::block::Block;
use core::coin::Coin;
use core::key::WalletKeyPair;
use core::transaction::{Transaction, SignedTransaction};
use ring::digest;
use serde_json;
use time;

pub struct Miner {
    pub miner_wallet: WalletKeyPair,
}

impl Miner {
    pub fn new() -> Self {
        Miner {
            miner_wallet: WalletKeyPair::new(),
        }
    }

    pub fn make_genesis(&self) -> Block {
        let t = self.now_millis();
        let signed = self.make_reward(t);
        Block::new(None, None, t, vec![signed], self.make_entropy())
    }
    
    pub fn mine_on(&self, parent: &Block, gp: Option<&Block>) -> Block {
        let t = self.now_millis();
        let signed = self.make_reward(t);

        let gp_ts = match gp {
            Some(b) => Some(b.unix_millis),
            None => None,
        };
        
        let mut b =
            Block::new(
                Some(parent),
                gp_ts,
                t,
                vec![signed],
                self.make_entropy());

        while !b.hash_meets_difficulty() {
            b.reset_mining_entropy(self.make_entropy());
        }

        println!("Found a block!: {}", serde_json::to_string(&b).unwrap());
        return b;
    }

    pub fn now_millis(&self) -> i64 {
        let now = time::now_utc().to_timespec();
        (now.sec * 1000) + (now.nsec / 1_000_000) as i64
    }

    pub fn make_entropy(&self) -> Vec<u8> {
        let foo = format!("{}", time::precise_time_s());
        digest::digest(&digest::SHA256, &foo.into_bytes()).as_ref().to_vec()
    }

    pub fn make_reward(&self, timestamp: i64) -> SignedTransaction {
        let reward = Transaction::new(
            Amount::units(100),
            Coin::Radcoin,
            None,
            self.miner_wallet.public_key(),
            timestamp);

        SignedTransaction::sign(reward, &self.miner_wallet)
    }
}
