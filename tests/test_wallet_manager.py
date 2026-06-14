from gamla_chain.core.wallet_manager import WalletManager


class FakePersistence:
    def __init__(self):
        self.store = {}
    def save(self, name, data):
        self.store[name] = data
    def load(self, name):
        return self.store.get(name)


class TestWalletManager:
    def setup_method(self):
        self.persist = FakePersistence()
        self.wm = WalletManager(self.persist)

    def test_create_wallet(self):
        wallet = self.wm.create_wallet("user-1", "My First Wallet")
        assert wallet["address"].startswith("0x")
        assert len(wallet["address"]) == 66
        assert len(wallet["private_key"]) == 64
        assert wallet["user_id"] == "user-1"
        assert wallet["label"] == "My First Wallet"

    def test_create_wallet_auto_label(self):
        wallet = self.wm.create_wallet("user-1")
        assert wallet["label"] == "Wallet #1"

    def test_get_user_wallets(self):
        self.wm.create_wallet("user-1", "Main")
        self.wm.create_wallet("user-1", "Savings")
        self.wm.create_wallet("user-2", "Other")
        wallets = self.wm.get_user_wallets("user-1")
        assert len(wallets) == 2
        assert wallets[0]["label"] == "Main"
        assert wallets[1]["label"] == "Savings"

    def test_get_wallet_by_address(self):
        created = self.wm.create_wallet("user-1", "Test")
        found = self.wm.get_wallet_by_address(created["address"])
        assert found is not None
        assert found["address"] == created["address"]
        assert found["private_key"] == created["private_key"]

    def test_get_nonexistent_wallet(self):
        assert self.wm.get_wallet_by_address("0xdeadbeef") is None

    def test_persistence_roundtrip(self):
        self.wm.create_wallet("user-1", "Saved")
        wm2 = WalletManager(self.persist)
        wallets = wm2.get_user_wallets("user-1")
        assert len(wallets) == 1
        assert wallets[0]["label"] == "Saved"
