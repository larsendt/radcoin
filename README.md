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

- Remove everything that's not needed from block config - lots of stuff that
can be derived from other info
- Block validation
    - Given new block + known chain, is new block valid?
        - Does it have a valid hash for the current difficulty?
        - Does it reference a parent already in the chain?
        - Are all non-reward transactions valid?
            - Signature matches
            - From-addr has enough to send
            - To-addr is non-null
        - Is the reward transaction valid?
            - Is there only one in the block?
            - Is the from addr null?
            - Is the to addr non-null?
            - Is the reward amount as expected?
instead of just parent-grandparent
- Better chain
    - Max heap to track head of chain
    - Validation methods
- Tune difficulty by averaging block mining time over a large number of blocks
- Storage
    - Chain
    - Rollup of chain for easy stats
- P2P
    - Need a well defined RPC thing for this - GRPC?
    - Connect to gateway
    - Discover peers
    - Request and send blocks
    - Request and send transactions
- Better wallet
- Bot to track chain stats
