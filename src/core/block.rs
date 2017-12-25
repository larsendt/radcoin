use core::block_config::BlockConfig;
use core::transaction::SignedTransaction;
use ring::digest;
use serde_json;

#[derive(Deserialize, Serialize)]
pub struct Block {
    pub block_num: u64,
    pub unix_millis: i64,
    pub config: BlockConfig,
    pub transactions: Vec<SignedTransaction>,
    pub parent_sha256: Vec<u8>,
    pub mining_entropy: Vec<u8>,
}

impl Block {
    pub fn new(
        parent: Option<&Block>,
        grandparent_unix_millis: Option<i64>,
        unix_millis: i64,
        transactions: Vec<SignedTransaction>,
        mining_entropy: Vec<u8>)
        -> Self {

        let parent_time = match parent {
            Some(p) => p.unix_millis,
            None => 0,
        };

        let parent_difficulty = match parent {
            Some(p) => p.config.difficulty,
            None => 0,
        };

        let parent_block_num = match parent {
            Some(p) => p.block_num,
            None => 0,
        };

        let gp_time;
        if parent_block_num <= 0 {
            if let Some(_) = grandparent_unix_millis {
                panic!("Parent block is <= 0 but gp timestamp specified");
            } else {
                gp_time = 0;
            }
        } else {
            if let Some(t) = grandparent_unix_millis {
                gp_time = t;
            } else {
                panic!("Parent block is > 0 but gp timestamp is None");
            }
        }

        let config = match parent {
            Some(_) => BlockConfig::with_timestamps(gp_time, parent_time, parent_difficulty),
            None => BlockConfig::genesis_config(),
        };

        if transactions.len() > config.max_transactions_per_block as usize {
            panic!("Too many transactions in the block!");
        }

        if mining_entropy.len() > config.max_mining_entropy_size as usize {
            panic!("Too much mining entropy!");
        }

        let parent_hash: Vec<u8> = match parent {
            Some(p) => p.hash(),
            None => vec![],
        };

        let block_num: u64 = match parent {
            Some(p) => p.block_num + 1,
            None => 0,
        };

        if unix_millis <= parent_time {
            panic!("New timestamp is before parent time!");
        }

        Block {
            block_num: block_num,
            unix_millis: unix_millis,
            config: config,
            transactions: transactions,
            parent_sha256: parent_hash,
            mining_entropy: mining_entropy,
        }
    }

    pub fn reset_mining_entropy(&mut self, mining_entropy: Vec<u8>) {
        if mining_entropy.len() > self.config.max_mining_entropy_size as usize {
            panic!("Too much mining entropy!");
        }

        self.mining_entropy = mining_entropy;
    }

    pub fn hash(&self) -> Vec<u8> {
        let serialized = serde_json::to_vec(self).unwrap(); 
        digest::digest(&digest::SHA256, &serialized).as_ref().to_vec()
    }

    pub fn hash_meets_difficulty(&self) -> bool {
        let h = self.hash();
        let num_zero_bytes = self.config.difficulty as usize / 8;
        let num_zero_bits = self.config.difficulty as usize - (num_zero_bytes * 8);
        let num_one_bits = 8 - num_zero_bits;

        if h.len() < (num_zero_bytes + 1) {
            panic!("Difficulty is too high!");
        }

        for b in 0..num_zero_bytes {
            if h[b] != 0 {
                return false;
            }
        }

        if h[num_zero_bytes] > (2u32.pow(num_one_bits as u32) - 1) as u8 {
            return false;
        } else {
            return true;
        }
    }
}
