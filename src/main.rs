extern crate ring;
extern crate untrusted;

mod wallet;
mod core;

use wallet::Wallet;
use core::amount::Amount;
use core::coin::Coin;

fn main() {
    let me = Wallet::new();
    let somebody = Wallet::new();
    let txn = me.transaction_to(
        &somebody.address(), Coin::Radcoin, Amount::units(1));
    println!("valid? {}", txn.signature_is_valid());
}
