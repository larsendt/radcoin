#[macro_use]
extern crate serde_derive;

extern crate base64;
extern crate ring;
extern crate serde;
extern crate serde_json;
extern crate untrusted;

mod wallet;
mod core;

use wallet::Wallet;
use core::amount::Amount;
use core::block::Block;
use core::coin::Coin;
use core::transaction::{Transaction, SignedTransaction};

fn main() {
    let me = Wallet::new();
    let somebody = Wallet::new();

    let txn = Transaction::new(
        Amount::units(1),
        Coin::Radcoin,
        me.address(),
        somebody.address(),
        0);

    let signed = SignedTransaction::sign(txn, &me.key_pair);
    let txns = vec![signed];

    let b = Block::new(None, None, 1, txns, vec![0]);
    println!("{}", serde_json::to_string(&b).unwrap());
    println!("hash: {:?}", b.hash());
    println!("diff: {}", b.hash_meets_difficulty());

    let txn2 = Transaction::new(
        Amount::units(1),
        Coin::Radcoin,
        me.address(),
        somebody.address(),
        0);
    let signed2 = SignedTransaction::sign(txn2, &me.key_pair);

    let txns2 = vec![signed2];

    let b2 = Block::new(Some(&b), None, 2, txns2, vec![0]);
    println!("{}", serde_json::to_string(&b2).unwrap());
    println!("hash: {:?}", b2.hash());
    println!("diff: {}", b2.hash_meets_difficulty());
}
