"""Simple wallet using SHA256 hashes as pseudonymous addresses."""
import hashlib
import secrets
from dataclasses import dataclass, field


@dataclass
class Wallet:
    private_key: str = field(default_factory=lambda: secrets.token_hex(32))
    address: str = ""

    def __post_init__(self):
        if not self.address:
            self.address = hashlib.sha256(self.private_key.encode()).hexdigest()

    def sign(self, message: str) -> str:
        return hashlib.sha256(f"{self.private_key}{message}".encode()).hexdigest()

    @classmethod
    def from_key(cls, private_key: str) -> "Wallet":
        wallet = cls(private_key=private_key)
        wallet.address = hashlib.sha256(private_key.encode()).hexdigest()
        return wallet
