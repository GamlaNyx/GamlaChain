import os
from dataclasses import dataclass

@dataclass
class Config:
    mining_difficulty: int = 4
    mining_reward: float = 50.0
    host: str = "127.0.0.1"
    port: int = 8000
    data_dir: str = "data"
    session_expiry_days: int = 7
    static_dir: str = "frontend"

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            mining_difficulty=int(os.getenv("MINING_DIFFICULTY", "4")),
            mining_reward=float(os.getenv("MINING_REWARD", "50.0")),
            host=os.getenv("HOST", "127.0.0.1"),
            port=int(os.getenv("PORT", "8000")),
            data_dir=os.getenv("DATA_DIR", "data"),
            session_expiry_days=int(os.getenv("SESSION_EXPIRY_DAYS", "7")),
            static_dir=os.getenv("STATIC_DIR", "frontend"),
        )

default_config = Config()
