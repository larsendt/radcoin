const NANOS_PER_UNIT: u64 = 1_000_000_000;

pub struct Amount {
    nanos: u64,
}

impl Amount {
    pub fn units(v: u64) -> Self {
        Amount {
            nanos: v * NANOS_PER_UNIT,
        }
    }
}
