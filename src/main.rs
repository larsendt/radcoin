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
    println!("signed txn: {}", String::from_utf8(signed.serialized_for_block()).unwrap());

    println!("valid? {}", signed.signature_is_valid());
}
