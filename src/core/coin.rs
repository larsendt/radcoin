pub enum Coin {
    Radcoin,
    ButtWaterToken 
}

impl Coin {
    pub fn serialize(&self) -> String {
        let s = match *self {
            Coin::Radcoin => "radcoin",
            Coin::ButtWaterToken => "buttwatertoken",
        };

        String::from(s)
    }
}
