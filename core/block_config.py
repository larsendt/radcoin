from core.serializable import Serializable, Ser

class BlockConfig(Serializable):
    def __init__(self, difficulty) -> None:
        self.difficulty = difficulty

    def serializable(self) -> Ser:
        return {
            "difficulty": self.difficulty,
        }

    @staticmethod
    def from_dict(obj: Ser) -> "BlockConfig":
        diff = obj["difficulty"]
        if diff < 0 or diff > 255:
            raise ValueError("Difficulty must be between 0 and 255")
        return BlockConfig(diff)
