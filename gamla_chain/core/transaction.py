import time
from dataclasses import dataclass, field

from gamla_chain.utils.crypto import hash_transaction


@dataclass
class Transaction:
    sender: str
    receiver: str
    amount: float
    timestamp: float = field(default_factory=time.time)
    tx_hash: str = ""

    def __post_init__(self):
        if not self.tx_hash:
            self.tx_hash = self.compute_hash()

    def compute_hash(self) -> str:
        return hash_transaction(
            self.sender, self.receiver, self.amount, self.timestamp
        )

    def to_dict(self) -> dict:
        return {
            "sender": self.sender,
            "receiver": self.receiver,
            "amount": self.amount,
            "timestamp": self.timestamp,
            "tx_hash": self.tx_hash,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Transaction":
        return cls(
            sender=data["sender"],
            receiver=data["receiver"],
            amount=data["amount"],
            timestamp=data["timestamp"],
            tx_hash=data.get("tx_hash", ""),
        )
