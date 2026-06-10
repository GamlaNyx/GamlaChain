import hashlib
import json
from typing import Any


def sha256(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


def hash_block(index: int, previous_hash: str, timestamp: float,
               transactions: list[dict[str, Any]], nonce: int) -> str:
    block_string = json.dumps(
        {
            "index": index,
            "previous_hash": previous_hash,
            "timestamp": timestamp,
            "transactions": transactions,
            "nonce": nonce,
        },
        sort_keys=True,
    )
    return sha256(block_string)


def hash_transaction(sender: str, receiver: str, amount: float,
                     timestamp: float) -> str:
    tx_string = json.dumps(
        {"sender": sender, "receiver": receiver, "amount": amount, "timestamp": timestamp},
        sort_keys=True,
    )
    return sha256(tx_string)
