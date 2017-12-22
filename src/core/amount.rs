const NANOS_PER_UNIT: u64 = 1_000_000_000;

pub struct Amount {
    pub nanos: u64,
}

impl Amount {
    pub fn units(v: u64) -> Self {
        Amount {
            nanos: v * NANOS_PER_UNIT,
        }
    }

    pub fn serialize(&self) -> String {
        format!("{}_nanos", self.nanos)
    }
}
