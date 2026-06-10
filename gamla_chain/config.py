import os
from dataclasses import dataclass, field


@dataclass
class Config:
    mining_difficulty: int = 4
    mining_reward: float = 50.0
    host: str = "127.0.0.1"
    port: int = 8000

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            mining_difficulty=int(os.getenv("MINING_DIFFICULTY", "4")),
            mining_reward=float(os.getenv("MINING_REWARD", "50.0")),
            host=os.getenv("HOST", "127.0.0.1"),
            port=int(os.getenv("PORT", "8000")),
        )


default_config = Config()
