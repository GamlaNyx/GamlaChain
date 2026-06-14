import time
from gamla_chain.core.auth import AuthManager, User, Session


class FakePersistence:
    def __init__(self):
        self.store = {}
    def save(self, name, data):
        self.store[name] = data
    def load(self, name):
        return self.store.get(name)


class TestAuthManager:
    def setup_method(self):
        self.persist = FakePersistence()
        self.auth = AuthManager(self.persist)

    def test_register_creates_user(self):
        # Register admin first (first user always gets admin role)
        self.auth.register("admin", "adminpass")
        # Second user gets "user" role
        user = self.auth.register("alice", "secret123")
        assert user.username == "alice"
        assert user.role == "user"
        assert user.password_hash != "secret123"
        assert len(user.id) == 32

    def test_register_duplicate_fails(self):
        self.auth.register("alice", "secret123")
        try:
            self.auth.register("alice", "other")
            assert False, "should have raised"
        except ValueError as e:
            assert "already exists" in str(e)

    def test_login_correct_password(self):
        self.auth.register("alice", "secret123")
        session = self.auth.login("alice", "secret123")
        assert session is not None
        assert len(session.token) == 32
        assert session.user_id == self.auth.users["alice"].id

    def test_login_wrong_password(self):
        self.auth.register("alice", "secret123")
        session = self.auth.login("alice", "wrong")
        assert session is None

    def test_login_nonexistent_user(self):
        assert self.auth.login("nobody", "pass") is None

    def test_get_user_by_token(self):
        self.auth.register("alice", "secret123")
        session = self.auth.login("alice", "secret123")
        user = self.auth.get_user_by_token(session.token)
        assert user is not None
        assert user.username == "alice"

    def test_get_user_by_invalid_token(self):
        assert self.auth.get_user_by_token("invalid-token") is None

    def test_logout(self):
        self.auth.register("alice", "secret123")
        session = self.auth.login("alice", "secret123")
        self.auth.logout(session.token)
        assert self.auth.get_user_by_token(session.token) is None

    def test_register_auto_creates_admin_if_first(self):
        user = self.auth.register("admin", "adminpass")
        assert user.role == "admin"
        user2 = self.auth.register("bob", "bobpass")
        assert user2.role == "user"

    def test_persistence_roundtrip(self):
        self.auth.register("alice", "secret123")
        self.auth.login("alice", "secret123")
        auth2 = AuthManager(self.persist)
        assert "alice" in auth2.users
        session = auth2.login("alice", "secret123")
        assert session is not None
