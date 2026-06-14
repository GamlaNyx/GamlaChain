import secrets
import hashlib
import time
from typing import Any


class WalletManager:
    """Manages user wallets — create, list, lookup."""

    def __init__(self, persistence):
        self._persist = persistence
        self.wallets: dict[str, dict[str, Any]] = {}  # keyed by address
        self._load()

    def _load(self) -> None:
        data = self._persist.load("wallets")
        if data:
            for w in data:
                self.wallets[w["address"]] = w

    def _save(self) -> None:
        self._persist.save("wallets", list(self.wallets.values()))

    def _generate_wallet(self) -> tuple[str, str]:
        private_key = secrets.token_hex(32)
        address = "0x" + hashlib.sha256(private_key.encode()).hexdigest()
        return private_key, address

    def create_wallet(self, user_id: str, label: str | None = None) -> dict:
        private_key, address = self._generate_wallet()
        count = len(self.get_user_wallets(user_id))
        wallet = {
            "address": address,
            "private_key": private_key,
            "user_id": user_id,
            "label": label or f"Wallet #{count + 1}",
            "created_at": time.time(),
        }
        self.wallets[address] = wallet
        self._save()
        return wallet

    def get_user_wallets(self, user_id: str) -> list[dict]:
        return [w for w in self.wallets.values() if w["user_id"] == user_id]

    def get_wallet_by_address(self, address: str) -> dict | None:
        return self.wallets.get(address)

    def get_all_addresses(self) -> list[str]:
        return list(self.wallets.keys())
