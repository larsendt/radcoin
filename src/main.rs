extern crate ring;
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
    let somebodys_addr = somebody.address();

    let txn = Transaction::new(
        Amount::units(1),
        Coin::Radcoin,
        &me.key_pair,
        &somebodys_addr,
        0);

    let signed = SignedTransaction::sign(txn);

    println!("valid? {}", signed.signature_is_valid());
}
