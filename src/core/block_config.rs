const VERSION_TAG: &str = "radcoin-2017-12-24";
const MAX_MINING_ENTROPY_SIZE: u16 = 32;
const MAX_TRANSACTIONS_PER_BLOCK: u32 = 256;
const ONE_MINUTE: i64 = 1 * 60 * 1000;
const THIRTY_SECONDS: i64 = 30 * 1000;
const RADCOIN_NANOS: u64 = 100 * 1_000_000_000;
const BWATER_TOKEN_NANOS: u64 = 100 * 1_000_000_000;

#[derive(Deserialize, Serialize, Clone)]
pub struct BlockConfig {
    pub version_tag: String,
    pub is_genesis: bool,
    pub difficulty: u8, // Number of prefix bits that must be zero
    pub max_mining_entropy_size: u16, // Bytes
    pub max_transactions_per_block: u32,
    pub difficulty_config: DifficultyConfig,
    pub reward_config: RewardConfig,
}

#[derive(Deserialize, Serialize, Clone)]
pub struct DifficultyConfig {
    // If the time between grandparent and parent is greater than this value,
    // subtract one from the parent's difficulty setting
    pub halve_gt_time_delta: i64, 
    // If the time between grandparent and parent is less than this value,
    // add one to the parent's difficulty setting
    pub double_gt_time_delta: i64,
}

#[derive(Deserialize, Serialize, Clone)]
pub struct RewardConfig {
    pub radcoin_nanos: u64,
    pub buttwater_token_nanos: u64,
}

impl BlockConfig {
    pub fn genesis_config() -> Self {
        BlockConfig {
            version_tag: String::from(VERSION_TAG),
            is_genesis: true,
            difficulty: 0,
            max_mining_entropy_size: MAX_MINING_ENTROPY_SIZE,
            max_transactions_per_block: MAX_TRANSACTIONS_PER_BLOCK,
            difficulty_config: DifficultyConfig {
                halve_gt_time_delta: ONE_MINUTE,
                double_gt_time_delta: THIRTY_SECONDS,
            },
            reward_config: RewardConfig {
                radcoin_nanos: RADCOIN_NANOS,
                buttwater_token_nanos: BWATER_TOKEN_NANOS,
            },
        }
    }

    pub fn with_timestamps(
        gp_timestamp: i64,
        parent_timestamp: i64,
        parent_difficulty: u8)
        -> Self {

        let difficulty;
        if parent_timestamp - gp_timestamp > ONE_MINUTE {
            if parent_difficulty > 0 {
                difficulty = parent_difficulty - 1;
            } else {
                difficulty = parent_difficulty;
            }
        } else if parent_timestamp - gp_timestamp < THIRTY_SECONDS {
            if parent_difficulty < 255 {
                difficulty = parent_difficulty + 1;
            } else {
                difficulty = parent_difficulty;
            }
        } else {
            difficulty = parent_difficulty;
        }

        BlockConfig {
            version_tag: String::from(VERSION_TAG),
            is_genesis: false,
            difficulty: difficulty,
            max_mining_entropy_size: MAX_MINING_ENTROPY_SIZE,
            max_transactions_per_block: MAX_TRANSACTIONS_PER_BLOCK,
            difficulty_config: DifficultyConfig {
                halve_gt_time_delta: ONE_MINUTE,
                double_gt_time_delta: THIRTY_SECONDS,
            },
            reward_config: RewardConfig {
                radcoin_nanos: RADCOIN_NANOS,
                buttwater_token_nanos: BWATER_TOKEN_NANOS,
            },
        }
    }
}

