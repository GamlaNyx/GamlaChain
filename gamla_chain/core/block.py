import time
from dataclasses import dataclass, field

from gamla_chain.core.transaction import Transaction
from gamla_chain.utils.crypto import hash_block


@dataclass
class Block:
    index: int
    previous_hash: str
    timestamp: float = field(default_factory=time.time)
    transactions: list[Transaction] = field(default_factory=list)
    nonce: int = 0
    hash: str = ""

    def compute_hash(self) -> str:
        return hash_block(
            self.index,
            self.previous_hash,
            self.timestamp,
            [tx.to_dict() for tx in self.transactions],
            self.nonce,
        )

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "nonce": self.nonce,
            "hash": self.hash,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Block":
        block = cls(
            index=data["index"],
            previous_hash=data["previous_hash"],
            timestamp=data["timestamp"],
            nonce=data["nonce"],
            hash=data.get("hash", ""),
        )
        block.transactions = [
            Transaction.from_dict(tx) for tx in data.get("transactions", [])
        ]
        return block
