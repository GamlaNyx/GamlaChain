"""End-to-end smoke test: register, login, create wallet, check balance."""
import tempfile
from fastapi.testclient import TestClient
from gamla_chain.core.persistence import PersistenceManager
from gamla_chain.core.auth import AuthManager
from gamla_chain.core.wallet_manager import WalletManager
from gamla_chain.core.blockchain_manager import manager
from gamla_chain.api.middleware import init_auth_middleware
from gamla_chain.api.routes_auth import init_auth_routes
from gamla_chain.api.routes_wallet import init_wallet_routes
from gamla_chain.api.routes_admin import init_admin_routes
from gamla_chain.api.server import create_app


class TestIntegration:
    @classmethod
    def setup_class(cls):
        cls.tmpdir = tempfile.mkdtemp()
        cls.persistence = PersistenceManager(data_dir=cls.tmpdir)
        cls.auth = AuthManager(cls.persistence)
        cls.wm = WalletManager(cls.persistence)
        cls.blockchain = manager.blockchain

        init_auth_middleware(cls.auth)
        init_auth_routes(cls.auth, cls.wm)
        init_wallet_routes(cls.wm, cls.blockchain)
        init_admin_routes(cls.auth, cls.wm, cls.blockchain)

        cls.app = create_app(static_dir="frontend")
        cls.client = TestClient(cls.app)
        cls._token = None

    @classmethod
    def teardown_class(cls):
        import shutil
        shutil.rmtree(cls.tmpdir, ignore_errors=True)

    @classmethod
    def _get_token(cls) -> str:
        """Ensure a user is registered and logged in, return token."""
        if cls._token is None:
            # Register admin first so testuser gets "user" role
            cls.client.post("/api/v1/auth/register", json={
                "username": "admin_first", "password": "adminpass"
            })
            cls.client.post("/api/v1/auth/register", json={
                "username": "testuser", "password": "testpass"
            })
            resp = cls.client.post("/api/v1/auth/login", json={
                "username": "testuser", "password": "testpass"
            })
            cls._token = resp.json()["token"]
        return cls._token

    def _headers(self):
        return {"Authorization": f"Bearer {self._get_token()}"}

    def test_register_and_login(self):
        token = self._get_token()
        assert len(token) == 32

    def test_chain_info_public(self):
        resp = self.client.get("/api/v1/chain/info")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert data["data"]["height"] >= 1

    def test_get_me_with_token(self):
        resp = self.client.get("/api/v1/auth/me", headers=self._headers())
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert len(data["wallets"]) >= 1

    def test_balance_of_new_wallet(self):
        me = self.client.get("/api/v1/auth/me", headers=self._headers())
        wallet_addr = me.json()["wallets"][0]["address"]
        resp = self.client.get(f"/api/v1/wallet/{wallet_addr}/balance")
        assert resp.status_code == 200
        assert resp.json()["balance"] == 0.0

    def test_create_second_wallet(self):
        resp = self.client.post("/api/v1/wallet/create", json={"label": "Savings"},
                                headers=self._headers())
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert data["wallet"]["label"] == "Savings"

        me = self.client.get("/api/v1/auth/me", headers=self._headers())
        assert len(me.json()["wallets"]) == 2

    def test_admin_endpoint_blocked_for_user(self):
        resp = self.client.get("/api/v1/admin/dashboard", headers=self._headers())
        assert resp.status_code == 403

    def test_chain_info_fields(self):
        resp = self.client.get("/api/v1/chain/info")
        assert resp.status_code == 200
        data = resp.json()
        assert "height" in data["data"]
        assert "difficulty" in data["data"]
        assert "mining_reward" in data["data"]
