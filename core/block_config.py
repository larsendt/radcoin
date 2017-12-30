from core.serializable import Serializable, Ser

DEFAULT_DIFFICULTY = 2

class BlockConfig(Serializable):
    def __init__(self) -> None:
        self.difficulty = DEFAULT_DIFFICULTY

    def serializable(self) -> Ser:
        return {
            "difficulty": self.difficulty,
        }
