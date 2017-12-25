use core::block::Block;

pub struct Chain {
    blocks: Vec<Block>
}

impl Chain {
    pub fn from_existing(blocks: Vec<Block>) -> Self {
        Chain {
            blocks: blocks
        }
    }

    pub fn head(&self) -> Block {
        if self.blocks.len() < 1 {
            panic!("Empty chain isn't allowed");
        }

        let i = self.blocks.len() - 1;
        self.blocks[i].clone()
    }

    pub fn grandparent(&self) -> Option<Block> {
        if self.blocks.len() >= 2 {
            let i = self.blocks.len() - 2;
            return Some(self.blocks[i].clone());
        } else {
            return None
        }
    }

    pub fn add_block(&mut self, block: Block) {
        self.blocks.push(block);
    }
}
