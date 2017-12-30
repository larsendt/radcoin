from core.serializable import Serializable, Ser

class BlockConfig(Serializable):
    def __init__(self, difficulty) -> None:
        self.difficulty = difficulty

    def serializable(self) -> Ser:
        return {
            "difficulty": self.difficulty,
        }
