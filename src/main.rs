#[macro_use]
extern crate serde_derive;

extern crate base64;
extern crate ring;
extern crate serde;
extern crate serde_json;
extern crate time;
extern crate untrusted;

mod core;
mod miner;
mod wallet;

use core::chain::Chain;
use miner::Miner;

fn main() {
    let m = Miner::new();
    let mut c = Chain::from_existing(vec![m.make_genesis()]);

    let dur = std::time::Duration::from_millis(1000);
    std::thread::sleep(dur);

    loop {
        let h = c.head();
        let gp = c.grandparent();


        match gp {
            Some(gp) => c.add_block(m.mine_on(&h, Some(&gp))),
            None => c.add_block(m.mine_on(&h, None)),
        }

        let dur = std::time::Duration::from_millis(1000);
        std::thread::sleep(dur);
    }
}
