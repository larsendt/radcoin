# Radcoin

## What does it do right now?

Not much. It mines a sequence of blocks with reward transactions. It doesn't do
network or storage.

## How do I run it?

1. Install rustup: https://rustup.rs
2. Maybe install rustc+cargo? I forget
3. Clone radcoin
4. `cd` to root of repo
5. `cargo run`

## Things to do

- Block validation
    - Given new block + known chain, is new block valid?
- Tune difficulty by averaging block mining time over a large number of blocks
instead of just parent-grandparent
- Better chain
    - Max heap to track head of chain
- Storage
    - Chain
    - Rollup of chain for easy stats
- P2P
    - Connect to gateway
    - Discover peers
    - Request and send blocks
    - Request and send transactions
- Better wallet
- Bot to track chain stats
