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
    cors_origins: str = "*"  # Comma-separated, e.g. "https://example.com,https://www.example.com"
    secret_key: str = ""     # Used for extra security; auto-generated if empty

    @classmethod
    def from_env(cls) -> "Config":
        import secrets
        return cls(
            mining_difficulty=int(os.getenv("MINING_DIFFICULTY", "4")),
            mining_reward=float(os.getenv("MINING_REWARD", "50.0")),
            host=os.getenv("HOST", "127.0.0.1"),
            port=int(os.getenv("PORT", "8000")),
            data_dir=os.getenv("DATA_DIR", "data"),
            session_expiry_days=int(os.getenv("SESSION_EXPIRY_DAYS", "7")),
            static_dir=os.getenv("STATIC_DIR", "frontend"),
            cors_origins=os.getenv("CORS_ORIGINS", "*"),
            secret_key=os.getenv("SECRET_KEY", secrets.token_hex(32)),
        )

default_config = Config()
