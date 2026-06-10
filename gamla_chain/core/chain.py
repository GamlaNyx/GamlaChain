import time
from dataclasses import dataclass, field
from urllib.parse import urlparse
from uuid import uuid4

import requests

from gamla_chain.config import default_config
from gamla_chain.core.block import Block
from gamla_chain.core.consensus import is_valid_proof, proof_of_work
from gamla_chain.core.transaction import Transaction
from gamla_chain.utils.crypto import hash_block


@dataclass
class Blockchain:
    chain: list[Block] = field(default_factory=list)
    pending_transactions: list[Transaction] = field(default_factory=list)
    difficulty: int = default_config.mining_difficulty
    mining_reward: float = default_config.mining_reward
    nodes: set[str] = field(default_factory=set)
    node_identifier: str = field(default_factory=lambda: str(uuid4()).replace("-", ""))

    def __post_init__(self):
        if not self.chain:
            self.chain = [self._create_genesis_block()]

    def _create_genesis_block(self) -> Block:
        genesis = Block(index=0, previous_hash="0")
        genesis = proof_of_work(genesis, self.difficulty)
        return genesis

    @property
    def last_block(self) -> Block:
        return self.chain[-1]

    def add_transaction(self, tx: Transaction) -> int:
        """Add a transaction to pending pool. Returns its index in the pool."""
        self.pending_transactions.append(tx)
        return len(self.pending_transactions) - 1

    def mine_pending_transactions(self, miner_address: str = "network") -> Block:
        """Mine all pending transactions into a new block, with coinbase reward first."""
        reward_tx = Transaction(
            sender="network", receiver=miner_address, amount=self.mining_reward
        )
        block = Block(
            index=len(self.chain),
            previous_hash=self.last_block.hash,
            transactions=[reward_tx] + list(self.pending_transactions),
        )
        block = proof_of_work(block, self.difficulty)
        self.chain.append(block)
        self.pending_transactions = []
        return block

    def is_chain_valid(self) -> bool:
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]
            if current.previous_hash != previous.hash:
                return False
            if not is_valid_proof(current, self.difficulty):
                return False
        return True

    def get_balance(self, address: str) -> float:
        balance = 0.0
        for block in self.chain:
            for tx in block.transactions:
                if tx.receiver == address:
                    balance += tx.amount
                if tx.sender == address:
                    balance -= tx.amount
        return balance

    def get_transaction_history(self, address: str) -> list[Transaction]:
        history: list[Transaction] = []
        for block in self.chain:
            for tx in block.transactions:
                if tx.sender == address or tx.receiver == address:
                    history.append(tx)
        return history

    def register_node(self, address: str) -> None:
        """Add a neighbouring node to the nodes set (idempotent via set)."""
        parsed = urlparse(address)
        netloc = parsed.netloc if parsed.netloc else parsed.path
        self.nodes.add(netloc)

    def valid_chain(self, chain: list[dict]) -> bool:
        """Validate an external chain (list of block dicts)."""
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]

            if block["previous_hash"] != last_block["hash"]:
                return False

            expected_hash = hash_block(
                block["index"],
                block["previous_hash"],
                block["timestamp"],
                block.get("transactions", []),
                block["nonce"],
            )
            if block["hash"] != expected_hash:
                return False
            if not block["hash"].startswith("0" * self.difficulty):
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self) -> bool:
        """Consensus algorithm: replace local chain with the longest valid one from neighbours."""
        new_chain: list[dict] | None = None
        max_length = len(self.chain)

        for node in self.nodes:
            try:
                resp = requests.get(f"http://{node}/api/v1/chain", timeout=5)
                if resp.status_code != 200:
                    continue
                payload = resp.json()
                chain_data = payload.get("data", payload)
                length = chain_data.get("length", 0)
                candidate = chain_data.get("chain", [])

                if length > max_length and self.valid_chain(candidate):
                    max_length = length
                    new_chain = candidate
            except requests.RequestException:
                continue

        if new_chain:
            self.chain = [Block.from_dict(b) for b in new_chain]
            return True
        return False

    def to_dict(self) -> dict:
        return {
            "length": len(self.chain),
            "chain": [b.to_dict() for b in self.chain],
            "pending_transactions": [tx.to_dict() for tx in self.pending_transactions],
            "difficulty": self.difficulty,
            "mining_reward": self.mining_reward,
            "nodes": list(self.nodes),
            "node_identifier": self.node_identifier,
        }
