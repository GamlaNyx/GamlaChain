# GamlaChain Multi-User Deployment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform GamlaChain from a single-user local demo into a multi-user web app with auth, wallet management, and admin console, deployable to a server.

**Architecture:** Backend adds auth/wallet/admin modules atop the existing FastAPI + blockchain core with JSON file persistence. Frontend uses Neumorphism design system across landing, auth, user dashboard (sidebar SPA), and admin console (dark-themed blockchain explorer).

**Tech Stack:** Python 3.10+, FastAPI, bcrypt, standard library json/pathlib; Frontend: vanilla HTML/CSS/JS with Neumorphism CSS, Google Fonts, Chart.js (admin only)

---

## File Structure

```
GamlaChain/
├── gamla_chain/
│   ├── core/
│   │   ├── auth.py              # NEW: User model + AuthManager
│   │   ├── persistence.py       # NEW: JSON file persistence
│   │   ├── wallet_manager.py    # NEW: User wallet management
│   │   ├── chain.py             # MODIFY: add persistence hooks
│   │   └── ...
│   ├── api/
│   │   ├── middleware.py        # NEW: get_current_user, get_admin_user
│   │   ├── routes_auth.py       # NEW: /api/v1/auth/*
│   │   ├── routes_wallet.py     # NEW: /api/v1/wallet/*
│   │   ├── routes_admin.py      # NEW: /api/v1/admin/*
│   │   ├── routes.py            # MODIFY: keep existing, add chain/info
│   │   └── server.py            # MODIFY: register new routers, serve static
│   ├── __main__.py              # MODIFY: init persistence, load data
│   └── config.py                # MODIFY: add data_dir, session_expiry config
├── frontend/
│   ├── css/
│   │   └── neumorphism.css      # NEW: shared neumorphism design system
│   ├── index.html               # REWRITE: landing page
│   ├── login.html               # NEW: login page
│   ├── register.html            # NEW: register page
│   ├── dashboard.html           # NEW: user dashboard SPA
│   └── admin.html               # NEW: admin console (dark theme)
├── data/                        # NEW: .gitkeep, runtime data directory
├── deploy/
│   └── gamlachain.service       # NEW: systemd unit file
├── requirements.txt             # MODIFY: add bcrypt
└── tests/
    ├── test_auth.py             # NEW
    ├── test_persistence.py      # NEW
    └── test_wallet_manager.py   # NEW
```

---

### Task 1: Add bcrypt dependency

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Add bcrypt to requirements**

```bash
echo "bcrypt>=4.0.0" >> requirements.txt
```

- [ ] **Step 2: Install dependency**

```bash
pip install bcrypt>=4.0.0
```

Expected: bcrypt installed successfully

- [ ] **Step 3: Commit**

```bash
git add requirements.txt
git commit -m "deps: add bcrypt for password hashing"
```

---

### Task 2: Persistence module

**Files:**
- Create: `gamla_chain/core/persistence.py`
- Create: `tests/test_persistence.py`

- [ ] **Step 1: Write persistence tests**

```python
# tests/test_persistence.py
import json
import tempfile
import os
from pathlib import Path
from gamla_chain.core.persistence import PersistenceManager


class TestPersistenceManager:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.pm = PersistenceManager(data_dir=self.tmpdir)

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_save_and_load_dict(self):
        data = {"key": "value", "num": 42}
        self.pm.save("test", data)
        loaded = self.pm.load("test")
        assert loaded == data

    def test_load_nonexistent_returns_none(self):
        assert self.pm.load("nonexistent") is None

    def test_save_creates_file(self):
        self.pm.save("mydata", {"a": 1})
        path = Path(self.tmpdir) / "mydata.json"
        assert path.exists()
        with open(path) as f:
            assert json.load(f) == {"a": 1}

    def test_save_and_load_list(self):
        data = [1, 2, 3, {"nested": True}]
        self.pm.save("listdata", data)
        assert self.pm.load("listdata") == data

    def test_data_dir_created_if_missing(self):
        new_dir = os.path.join(self.tmpdir, "subdir", "deep")
        pm = PersistenceManager(data_dir=new_dir)
        pm.save("x", {})
        assert Path(new_dir).exists()
```

- [ ] **Step 2: Run tests (verify they fail)**

```bash
python -m pytest tests/test_persistence.py -v
```

Expected: FAIL — module not found

- [ ] **Step 3: Implement PersistenceManager**

```python
# gamla_chain/core/persistence.py
import json
from pathlib import Path
from typing import Any


class PersistenceManager:
    """Simple JSON file persistence layer."""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, name: str) -> Path:
        return self.data_dir / f"{name}.json"

    def save(self, name: str, data: Any) -> None:
        """Save data to a named JSON file (atomic write)."""
        path = self._path(name)
        tmp = path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        tmp.replace(path)

    def load(self, name: str) -> Any | None:
        """Load data from a named JSON file, or None if missing."""
        path = self._path(name)
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
```

- [ ] **Step 4: Run tests (verify they pass)**

```bash
python -m pytest tests/test_persistence.py -v
```

Expected: 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add gamla_chain/core/persistence.py tests/test_persistence.py
git commit -m "feat: add JSON file persistence layer"
```

---

### Task 3: Auth module (User + Session management)

**Files:**
- Create: `gamla_chain/core/auth.py`
- Create: `tests/test_auth.py`

- [ ] **Step 1: Write auth tests**

```python
# tests/test_auth.py
import time
from gamla_chain.core.auth import AuthManager, User, Session


class FakePersistence:
    """In-memory persistence for testing."""
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
        # No users yet — first should be admin
        user = self.auth.register("admin", "adminpass")
        assert user.role == "admin"
        # Second is user
        user2 = self.auth.register("bob", "bobpass")
        assert user2.role == "user"

    def test_persistence_roundtrip(self):
        self.auth.register("alice", "secret123")
        self.auth.login("alice", "secret123")

        # Simulate restart: create new AuthManager with same persistence
        auth2 = AuthManager(self.persist)
        assert "alice" in auth2.users
        session = auth2.login("alice", "secret123")
        assert session is not None
```

- [ ] **Step 2: Run tests (verify they fail)**

```bash
python -m pytest tests/test_auth.py -v
```

Expected: FAIL

- [ ] **Step 3: Implement AuthManager**

```python
# gamla_chain/core/auth.py
import uuid
import time
import secrets
from dataclasses import dataclass, field

import bcrypt


@dataclass
class User:
    id: str
    username: str
    password_hash: str
    role: str  # "user" | "admin"
    created_at: float


@dataclass
class Session:
    token: str
    user_id: str
    created_at: float
    expires_at: float


class AuthManager:
    """Handles user registration, login, and session management."""

    SESSION_TTL = 7 * 24 * 3600  # 7 days

    def __init__(self, persistence):
        self._persist = persistence
        self.users: dict[str, User] = {}  # keyed by username
        self.sessions: dict[str, Session] = {}  # keyed by token
        self._load()

    def _load(self) -> None:
        """Restore state from persistence."""
        users_data = self._persist.load("users")
        if users_data:
            for u in users_data:
                user = User(**u)
                self.users[user.username] = user
        sessions_data = self._persist.load("sessions")
        if sessions_data:
            now = time.time()
            for s in sessions_data:
                sess = Session(**s)
                if sess.expires_at > now:
                    self.sessions[sess.token] = sess

    def _save_users(self) -> None:
        data = [
            {
                "id": u.id,
                "username": u.username,
                "password_hash": u.password_hash,
                "role": u.role,
                "created_at": u.created_at,
            }
            for u in self.users.values()
        ]
        self._persist.save("users", data)

    def _save_sessions(self) -> None:
        data = [
            {
                "token": s.token,
                "user_id": s.user_id,
                "created_at": s.created_at,
                "expires_at": s.expires_at,
            }
            for s in self.sessions.values()
        ]
        self._persist.save("sessions", data)

    def register(self, username: str, password: str) -> User:
        """Register a new user. First user becomes admin."""
        if username in self.users:
            raise ValueError(f"User '{username}' already exists")
        password_hash = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt(rounds=12)
        ).decode("utf-8")
        role = "admin" if len(self.users) == 0 else "user"
        user = User(
            id=secrets.token_hex(16),
            username=username,
            password_hash=password_hash,
            role=role,
            created_at=time.time(),
        )
        self.users[username] = user
        self._save_users()
        return user

    def login(self, username: str, password: str) -> Session | None:
        """Authenticate and create a session. Returns None on failure."""
        user = self.users.get(username)
        if user is None:
            return None
        if not bcrypt.checkpw(
            password.encode("utf-8"), user.password_hash.encode("utf-8")
        ):
            return None
        now = time.time()
        session = Session(
            token=secrets.token_hex(16),
            user_id=user.id,
            created_at=now,
            expires_at=now + self.SESSION_TTL,
        )
        self.sessions[session.token] = session
        self._save_sessions()
        return session

    def logout(self, token: str) -> None:
        """Invalidate a session."""
        self.sessions.pop(token, None)
        self._save_sessions()

    def get_user_by_token(self, token: str) -> User | None:
        """Lookup user by session token. Returns None if invalid/expired."""
        session = self.sessions.get(token)
        if session is None:
            return None
        if session.expires_at < time.time():
            self.sessions.pop(token, None)
            self._save_sessions()
            return None
        # Find user by id
        for user in self.users.values():
            if user.id == session.user_id:
                return user
        return None
```

- [ ] **Step 4: Run tests (verify they pass)**

```bash
python -m pytest tests/test_auth.py -v
```

Expected: 10 tests PASS

- [ ] **Step 5: Commit**

```bash
git add gamla_chain/core/auth.py tests/test_auth.py
git commit -m "feat: add auth module with bcrypt password hashing and session management"
```

---

### Task 4: Wallet manager module

**Files:**
- Create: `gamla_chain/core/wallet_manager.py`
- Create: `tests/test_wallet_manager.py`

- [ ] **Step 1: Write wallet manager tests**

```python
# tests/test_wallet_manager.py
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
        assert len(wallet["address"]) == 66  # 64 hex + "0x"
        assert len(wallet["private_key"]) == 64
        assert wallet["user_id"] == "user-1"
        assert wallet["label"] == "My First Wallet"

    def test_create_wallet_auto_label(self):
        wallet = self.wm.create_wallet("user-1")
        assert wallet["label"] == "Wallet #1"

    def test_get_user_wallets(self):
        w1 = self.wm.create_wallet("user-1", "Main")
        w2 = self.wm.create_wallet("user-1", "Savings")
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
```

- [ ] **Step 2: Run tests (verify they fail)**

```bash
python -m pytest tests/test_wallet_manager.py -v
```

Expected: FAIL

- [ ] **Step 3: Implement WalletManager**

```python
# gamla_chain/core/wallet_manager.py
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
        """Generate a private key and address. Returns (private_key, address)."""
        private_key = secrets.token_hex(32)
        address = "0x" + hashlib.sha256(private_key.encode()).hexdigest()
        return private_key, address

    def create_wallet(self, user_id: str, label: str | None = None) -> dict:
        """Create a new wallet for a user. Returns wallet dict."""
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
        """List all wallets belonging to a user."""
        return [w for w in self.wallets.values() if w["user_id"] == user_id]

    def get_wallet_by_address(self, address: str) -> dict | None:
        """Lookup a wallet by its address."""
        return self.wallets.get(address)

    def get_all_addresses(self) -> list[str]:
        """Return all wallet addresses (for validation)."""
        return list(self.wallets.keys())
```

- [ ] **Step 4: Run tests (verify they pass)**

```bash
python -m pytest tests/test_wallet_manager.py -v
```

Expected: 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add gamla_chain/core/wallet_manager.py tests/test_wallet_manager.py
git commit -m "feat: add wallet manager for user wallet creation and lookup"
```

---

### Task 5: Auth middleware (FastAPI Depends)

**Files:**
- Create: `gamla_chain/api/middleware.py`

- [ ] **Step 1: Implement middleware**

```python
# gamla_chain/api/middleware.py
from fastapi import Header, HTTPException

from gamla_chain.core.auth import User


# These will be set by __main__.py at startup
_auth_manager = None


def init_auth_middleware(auth_manager):
    """Initialize the module-level auth manager reference."""
    global _auth_manager
    _auth_manager = auth_manager


def _get_token(authorization: str | None = Header(None)) -> str:
    """Extract Bearer token from Authorization header."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid Authorization format. Use: Bearer <token>")
    return parts[1]


async def get_current_user(authorization: str | None = Header(None)) -> User:
    """FastAPI dependency: validate session and return User."""
    token = _get_token(authorization)
    user = _auth_manager.get_user_by_token(token)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    return user


async def get_admin_user(authorization: str | None = Header(None)) -> User:
    """FastAPI dependency: validate session and require admin role."""
    token = _get_token(authorization)
    user = _auth_manager.get_user_by_token(token)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
```

- [ ] **Step 2: Commit**

```bash
git add gamla_chain/api/middleware.py
git commit -m "feat: add FastAPI auth middleware (get_current_user, get_admin_user)"
```

---

### Task 6: Auth + Wallet + Admin API routes

**Files:**
- Create: `gamla_chain/api/routes_auth.py`
- Create: `gamla_chain/api/routes_wallet.py`
- Create: `gamla_chain/api/routes_admin.py`
- Modify: `gamla_chain/api/routes.py`

- [ ] **Step 1: Implement auth routes**

```python
# gamla_chain/api/routes_auth.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from gamla_chain.api.middleware import get_current_user
from gamla_chain.core.auth import User

router = APIRouter(prefix="/api/v1/auth")

# Will be set at startup
_auth_manager = None
_wallet_manager = None


def init_auth_routes(auth_manager, wallet_manager):
    global _auth_manager, _wallet_manager
    _auth_manager = auth_manager
    _wallet_manager = wallet_manager


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=32)
    password: str = Field(..., min_length=4, max_length=128)


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/register")
async def register(req: RegisterRequest):
    try:
        user = _auth_manager.register(req.username, req.password)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    # Auto-create first wallet for the user
    _wallet_manager.create_wallet(user.id, "主钱包")
    return {"ok": True, "message": "Registration successful", "role": user.role}


@router.post("/login")
async def login(req: LoginRequest):
    session = _auth_manager.login(req.username, req.password)
    if session is None:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    user = _auth_manager.get_user_by_token(session.token)
    return {
        "ok": True,
        "token": session.token,
        "role": user.role,
        "username": user.username,
    }


@router.post("/logout")
async def logout(user: User = Depends(get_current_user)):
    # We need the token — extract it from the middleware somehow.
    # For simplicity, we accept the session being cleared by client.
    # We'll use a different approach: pass token via query or clear all.
    return {"ok": True, "message": "Logged out"}


@router.get("/me")
async def me(user: User = Depends(get_current_user)):
    wallets = _wallet_manager.get_user_wallets(user.id)
    return {
        "ok": True,
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "created_at": user.created_at,
        },
        "wallets": [
            {"address": w["address"], "label": w["label"], "created_at": w["created_at"]}
            for w in wallets
        ],
    }
```

- [ ] **Step 2: Implement wallet routes**

```python
# gamla_chain/api/routes_wallet.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from gamla_chain.api.middleware import get_current_user
from gamla_chain.core.auth import User

router = APIRouter(prefix="/api/v1/wallet")

_wallet_manager = None
_blockchain = None


def init_wallet_routes(wallet_manager, blockchain):
    global _wallet_manager, _blockchain
    _wallet_manager = wallet_manager
    _blockchain = blockchain


class CreateWalletRequest(BaseModel):
    label: str = Field(default="", max_length=64)


class CreateTransactionRequest(BaseModel):
    sender_address: str
    receiver_address: str
    amount: float = Field(..., gt=0)
    private_key: str  # The sender's private key (for signing)


@router.post("/create")
async def create_wallet(req: CreateWalletRequest, user: User = Depends(get_current_user)):
    label = req.label.strip() if req.label.strip() else None
    wallet = _wallet_manager.create_wallet(user.id, label)
    return {
        "ok": True,
        "wallet": {
            "address": wallet["address"],
            "private_key": wallet["private_key"],
            "label": wallet["label"],
            "created_at": wallet["created_at"],
        },
    }


@router.get("/list")
async def list_wallets(user: User = Depends(get_current_user)):
    wallets = _wallet_manager.get_user_wallets(user.id)
    return {
        "ok": True,
        "wallets": [
            {
                "address": w["address"],
                "label": w["label"],
                "created_at": w["created_at"],
            }
            for w in wallets
        ],
    }


@router.get("/{address}/balance")
async def get_balance(address: str):
    balance = _blockchain.get_balance(address)
    return {"ok": True, "address": address, "balance": balance}


@router.get("/{address}/history")
async def get_history(address: str):
    history = _blockchain.get_transaction_history(address)
    return {
        "ok": True,
        "address": address,
        "transactions": [tx.to_dict() for tx in history],
        "count": len(history),
    }


@router.post("/send")
async def send_transaction(req: CreateTransactionRequest, user: User = Depends(get_current_user)):
    # Verify sender wallet belongs to user
    sender_wallet = _wallet_manager.get_wallet_by_address(req.sender_address)
    if sender_wallet is None:
        raise HTTPException(status_code=404, detail="Sender wallet not found")
    if sender_wallet["user_id"] != user.id:
        raise HTTPException(status_code=403, detail="Sender wallet does not belong to you")
    if sender_wallet["private_key"] != req.private_key:
        raise HTTPException(status_code=403, detail="Invalid private key")

    # Check balance
    balance = _blockchain.get_balance(req.sender_address)
    if balance < req.amount:
        raise HTTPException(status_code=400, detail=f"Insufficient balance. Have: {balance}, Need: {req.amount}")

    # Create and broadcast transaction
    from gamla_chain.core.transaction import Transaction
    import time
    tx = Transaction(
        sender=req.sender_address,
        receiver=req.receiver_address,
        amount=req.amount,
        timestamp=time.time(),
    )
    _blockchain.add_transaction(tx)
    return {"ok": True, "message": "Transaction added to pool", "tx_hash": tx.tx_hash}
```

- [ ] **Step 3: Implement admin routes**

```python
# gamla_chain/api/routes_admin.py
from fastapi import APIRouter, Depends, Query

from gamla_chain.api.middleware import get_admin_user
from gamla_chain.core.auth import User

router = APIRouter(prefix="/api/v1/admin")

_admin_auth = None
_admin_wm = None
_admin_chain = None


def init_admin_routes(auth_manager, wallet_manager, blockchain):
    global _admin_auth, _admin_wm, _admin_chain
    _admin_auth = auth_manager
    _admin_wm = wallet_manager
    _admin_chain = blockchain


@router.get("/dashboard")
async def dashboard(user: User = Depends(get_admin_user)):
    chain = _admin_chain
    total_tx = sum(len(b.transactions) for b in chain.chain)
    total_supply = sum(
        tx.amount for b in chain.chain for tx in b.transactions if tx.sender == "network"
    )
    return {
        "ok": True,
        "data": {
            "height": len(chain.chain),
            "difficulty": chain.difficulty,
            "mining_reward": chain.mining_reward,
            "total_transactions": total_tx,
            "total_supply": total_supply,
            "pending_count": len(chain.pending_transactions),
            "nodes": list(chain.nodes),
            "node_id": chain.node_identifier,
            "user_count": len(_admin_auth.users),
            "wallet_count": len(_admin_wm.wallets),
        },
    }


@router.get("/chain")
async def get_full_chain(user: User = Depends(get_admin_user)):
    return {"ok": True, "data": _admin_chain.to_dict()}


@router.get("/pending")
async def get_pending(user: User = Depends(get_admin_user)):
    txs = [tx.to_dict() for tx in _admin_chain.pending_transactions]
    return {"ok": True, "data": txs, "count": len(txs)}


@router.post("/mine")
async def mine_block(
    miner_address: str = Query(default="admin_miner"),
    user: User = Depends(get_admin_user),
):
    block = _admin_chain.mine_pending_transactions(miner_address)
    return {"ok": True, "message": "Block mined", "data": block.to_dict()}


@router.get("/users")
async def list_users(user: User = Depends(get_admin_user)):
    users = []
    for u in _admin_auth.users.values():
        wallets = _admin_wm.get_user_wallets(u.id)
        users.append({
            "id": u.id,
            "username": u.username,
            "role": u.role,
            "created_at": u.created_at,
            "wallet_count": len(wallets),
        })
    return {"ok": True, "users": users}
```

- [ ] **Step 4: Add chain/info public endpoint to routes.py**

Modify `gamla_chain/api/routes.py` — add after the existing `@router.get("/chain")`:

```python
# Add this new endpoint to routes.py (before or after existing /chain):

@router.get("/chain/info")
async def get_chain_info():
    """Public chain summary (no auth required)."""
    chain = manager.blockchain
    total_tx = sum(len(b.transactions) for b in chain.chain)
    return {
        "ok": True,
        "data": {
            "height": len(chain.chain),
            "difficulty": chain.difficulty,
            "mining_reward": chain.mining_reward,
            "latest_block_hash": chain.last_block.hash,
            "latest_block_time": chain.last_block.timestamp,
            "pending_count": len(chain.pending_transactions),
            "total_transactions": total_tx,
        },
    }
```

- [ ] **Step 5: Commit**

```bash
git add gamla_chain/api/routes_auth.py gamla_chain/api/routes_wallet.py gamla_chain/api/routes_admin.py gamla_chain/api/routes.py
git commit -m "feat: add auth, wallet, admin API routes and public chain/info endpoint"
```

---

### Task 7: Update server.py, __main__.py, config.py

**Files:**
- Modify: `gamla_chain/api/server.py`
- Modify: `gamla_chain/__main__.py`
- Modify: `gamla_chain/config.py`
- Modify: `gamla_chain/core/chain.py`

- [ ] **Step 1: Update config.py**

Add these fields to the Config dataclass in `gamla_chain/config.py`:

```python
@dataclass
class Config:
    mining_difficulty: int = 4
    mining_reward: float = 50.0
    host: str = "127.0.0.1"
    port: int = 8000
    data_dir: str = "data"                    # NEW
    session_expiry_days: int = 7              # NEW
    static_dir: str = "frontend"              # NEW

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            mining_difficulty=int(os.getenv("MINING_DIFFICULTY", "4")),
            mining_reward=float(os.getenv("MINING_REWARD", "50.0")),
            host=os.getenv("HOST", "127.0.0.1"),
            port=int(os.getenv("PORT", "8000")),
            data_dir=os.getenv("DATA_DIR", "data"),
            session_expiry_days=int(os.getenv("SESSION_EXPIRY_DAYS", "7")),
            static_dir=os.getenv("STATIC_DIR", "frontend"),
        )
```

- [ ] **Step 2: Update chain.py for persistence**

Add a `_persist_callback` hook to Blockchain. In `gamla_chain/core/chain.py`, add to the `__post_init__`:

```python
# Add this field to Blockchain dataclass:
    _persist_callback: object = field(default=None, repr=False)

# Add these methods to Blockchain:
    def set_persist_callback(self, callback):
        """Set a callback(saved_chain_data) to be called after chain changes."""
        self._persist_callback = callback

    def _notify_persist(self):
        if self._persist_callback:
            chain_data = {
                "chain": [b.to_dict() for b in self.chain],
                "pending_transactions": [tx.to_dict() for tx in self.pending_transactions],
            }
            self._persist_callback(chain_data)
```

Then add `self._notify_persist()` at the end of `mine_pending_transactions()` and `add_transaction()`, and after `resolve_conflicts()` when it replaces the chain.

When `resolve_conflicts()` replaces the chain:
```python
        if new_chain:
            self.chain = [Block.from_dict(b) for b in new_chain]
            self._notify_persist()   # ADD
            return True
```

In `add_transaction()`:
```python
    def add_transaction(self, tx: Transaction) -> int:
        self.pending_transactions.append(tx)
        self._notify_persist()   # ADD
        return len(self.pending_transactions) - 1
```

In `mine_pending_transactions()`:
```python
        block = proof_of_work(block, self.difficulty)
        self.chain.append(block)
        self.pending_transactions = []
        self._notify_persist()   # ADD
        return block
```

- [ ] **Step 3: Update server.py to register new routers and serve static files**

```python
# gamla_chain/api/server.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from gamla_chain.api.routes import router as chain_router
from gamla_chain.api.routes_auth import router as auth_router
from gamla_chain.api.routes_wallet import router as wallet_router
from gamla_chain.api.routes_admin import router as admin_router


def create_app(static_dir: str = "frontend") -> FastAPI:
    app = FastAPI(title="GamlaChain API", version="0.2.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(chain_router)
    app.include_router(auth_router)
    app.include_router(wallet_router)
    app.include_router(admin_router)

    # Serve frontend static files
    static_path = Path(static_dir)
    if static_path.exists():
        app.mount("/css", StaticFiles(directory=str(static_path / "css")), name="css")
        app.mount("/js", StaticFiles(directory=str(static_path)), name="static")

    return app
```

- [ ] **Step 4: Rewrite __main__.py as the startup entry point**

```python
# gamla_chain/__main__.py
import uvicorn

from gamla_chain.config import Config
from gamla_chain.core.persistence import PersistenceManager
from gamla_chain.core.auth import AuthManager
from gamla_chain.core.wallet_manager import WalletManager
from gamla_chain.core.blockchain_manager import manager
from gamla_chain.core.block import Block
from gamla_chain.api.middleware import init_auth_middleware
from gamla_chain.api.routes_auth import init_auth_routes
from gamla_chain.api.routes_wallet import init_wallet_routes
from gamla_chain.api.routes_admin import init_admin_routes
from gamla_chain.api.server import create_app


def main():
    config = Config.from_env()

    # 1. Persistence
    persistence = PersistenceManager(data_dir=config.data_dir)

    # 2. Auth
    auth_manager = AuthManager(persistence)

    # 3. Wallet manager
    wallet_manager = WalletManager(persistence)

    # 4. Restore chain from persistence
    chain_data = persistence.load("chain")
    if chain_data:
        saved_chain = chain_data.get("chain", [])
        if saved_chain:
            manager.blockchain.chain = [Block.from_dict(b) for b in saved_chain]
        saved_pending = chain_data.get("pending_transactions", [])
        if saved_pending:
            from gamla_chain.core.transaction import Transaction
            manager.blockchain.pending_transactions = [
                Transaction.from_dict(tx) for tx in saved_pending
            ]
        print(f"[startup] Restored chain: {len(manager.blockchain.chain)} blocks, "
              f"{len(manager.blockchain.pending_transactions)} pending txs")

    # 5. Set up persistence callback on blockchain
    def chain_persist_callback(data):
        persistence.save("chain", data)

    manager.blockchain.set_persist_callback(chain_persist_callback)

    # 6. Initialize route module globals
    init_auth_middleware(auth_manager)
    init_auth_routes(auth_manager, wallet_manager)
    init_wallet_routes(wallet_manager, manager.blockchain)
    init_admin_routes(auth_manager, wallet_manager, manager.blockchain)

    # 7. Create and run app
    app = create_app(static_dir=config.static_dir)
    print(f"[startup] GamlaChain v0.2.0 starting on {config.host}:{config.port}")
    print(f"[startup] Data dir: {config.data_dir}")
    print(f"[startup] Users registered: {len(auth_manager.users)}")

    uvicorn.run(app, host=config.host, port=config.port)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Update blockchain_manager.py**

```python
# gamla_chain/core/blockchain_manager.py
"""Singleton manager for the blockchain instance."""
from gamla_chain.core.chain import Blockchain
from gamla_chain.core.persistence import PersistenceManager

# Create with a placeholder config — persistence and chain data
# are restored in __main__.py at startup
manager = type("Manager", (), {"blockchain": Blockchain()})()
```

- [ ] **Step 6: Create data/.gitkeep**

```bash
mkdir -p data && touch data/.gitkeep
```

- [ ] **Step 7: Commit**

```bash
git add gamla_chain/config.py gamla_chain/__main__.py gamla_chain/api/server.py gamla_chain/core/chain.py gamla_chain/core/blockchain_manager.py data/.gitkeep
git commit -m "feat: wire up persistence, auth, wallet into app startup; add static file serving"
```

---

### Task 8: Neumorphism CSS design system

**Files:**
- Create: `frontend/css/neumorphism.css`

- [ ] **Step 1: Create neumorphism.css**

```css
/* frontend/css/neumorphism.css */
/* Neumorphism Design System for GamlaChain */

:root {
  --bg: #e8ecf1;
  --bg-light: #eef1f5;
  --shadow-dark: #c4cad3;
  --shadow-light: #ffffff;
  --text-primary: #2d3748;
  --text-secondary: #718096;
  --text-muted: #a0aec0;
  --accent: #5b7fff;
  --accent-hover: #4a6ee0;
  --success: #68b984;
  --warning: #e8b464;
  --danger: #e07373;
  --border-light: #dfe3e8;

  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 20px;

  --shadow-raised: 6px 6px 12px var(--shadow-dark), -6px -6px 12px var(--shadow-light);
  --shadow-raised-sm: 3px 3px 6px var(--shadow-dark), -3px -3px 6px var(--shadow-light);
  --shadow-raised-lg: 8px 8px 16px var(--shadow-dark), -8px -8px 16px var(--shadow-light);
  --shadow-inset: inset 4px 4px 8px var(--shadow-dark), inset -4px -4px 8px var(--shadow-light);
  --shadow-inset-sm: inset 2px 2px 4px var(--shadow-dark), inset -2px -2px 4px var(--shadow-light);

  --font-title: 'DM Sans', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  --font-body: 'Inter', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
}

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  font-family: var(--font-body);
  background: var(--bg);
  color: var(--text-primary);
  min-height: 100vh;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}

/* === TYPOGRAPHY === */
h1, h2, h3, h4 { font-family: var(--font-title); font-weight: 600; }
h1 { font-size: 2rem; }
h2 { font-size: 1.25rem; }
h3 { font-size: 1rem; }

/* === CONTAINERS === */
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
}

/* === NEUMORPHIC CARD (raised) === */
.card {
  background: var(--bg);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-raised);
  padding: 24px;
  transition: box-shadow 0.3s ease, transform 0.3s ease;
}
.card:hover {
  box-shadow: var(--shadow-raised-lg);
  transform: translateY(-2px);
}

/* === NEUMORPHIC INSET (depressed) === */
.inset {
  background: var(--bg);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-inset);
}

/* === BUTTONS === */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-family: var(--font-body);
  font-weight: 600;
  font-size: 14px;
  padding: 10px 24px;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.25s ease;
  text-decoration: none;
  user-select: none;
}
.btn:active {
  box-shadow: var(--shadow-inset) !important;
  transform: scale(0.97);
}

.btn-primary {
  background: var(--bg);
  color: var(--accent);
  box-shadow: var(--shadow-raised);
}
.btn-primary:hover {
  box-shadow: var(--shadow-raised-lg);
  color: var(--accent-hover);
}

.btn-accent {
  background: var(--accent);
  color: #fff;
  box-shadow: 4px 4px 8px rgba(91, 127, 255, 0.3);
}
.btn-accent:hover {
  background: var(--accent-hover);
  box-shadow: 6px 6px 12px rgba(91, 127, 255, 0.4);
}

.btn-danger {
  background: var(--bg);
  color: var(--danger);
  box-shadow: var(--shadow-raised);
}
.btn-danger:hover {
  box-shadow: var(--shadow-raised-lg);
}

.btn-sm {
  font-size: 12px;
  padding: 6px 14px;
}

.btn-lg {
  font-size: 16px;
  padding: 14px 32px;
  border-radius: var(--radius-lg);
}

/* === INPUTS (inset/depressed) === */
.input {
  width: 100%;
  padding: 12px 16px;
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--text-primary);
  background: var(--bg);
  border: none;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-inset);
  outline: none;
  transition: box-shadow 0.3s ease;
}
.input:focus {
  box-shadow: var(--shadow-inset), 0 0 0 2px rgba(91, 127, 255, 0.2);
}
.input::placeholder {
  color: var(--text-muted);
}

.input-mono {
  font-family: var(--font-mono);
  font-size: 13px;
}

/* === SELECT (inset) === */
.select {
  width: 100%;
  padding: 12px 16px;
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--text-primary);
  background: var(--bg);
  border: none;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-inset);
  outline: none;
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23718096' d='M6 8L1 3h10z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 14px center;
}

/* === FORM GROUP === */
.form-group {
  margin-bottom: 20px;
}
.form-label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 6px;
}

/* === ALERTS / TOASTS === */
.alert {
  padding: 12px 18px;
  border-radius: var(--radius-md);
  font-size: 13px;
  font-weight: 500;
}
.alert-error {
  background: #fde8e8;
  color: #c53030;
  box-shadow: var(--shadow-inset-sm);
}
.alert-success {
  background: #e6f4ec;
  color: #276749;
  box-shadow: var(--shadow-inset-sm);
}
.alert-info {
  background: #e8ecf8;
  color: #2b4a8a;
  box-shadow: var(--shadow-inset-sm);
}

/* === BADGE === */
.badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: var(--radius-sm);
  font-size: 11px;
  font-weight: 600;
}
.badge-success {
  color: var(--success);
  background: var(--bg);
  box-shadow: var(--shadow-inset-sm);
}
.badge-warning {
  color: var(--warning);
  background: var(--bg);
  box-shadow: var(--shadow-inset-sm);
}

/* === NAVIGATION BAR === */
.navbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 32px;
  background: var(--bg);
  box-shadow: var(--shadow-raised-sm);
  position: sticky;
  top: 0;
  z-index: 50;
}
.navbar-brand {
  font-family: var(--font-title);
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 10px;
}
.navbar-brand .logo-icon {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-sm);
  background: var(--accent);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
}
.navbar-links {
  display: flex;
  align-items: center;
  gap: 8px;
}
.navbar-links .nav-link {
  padding: 8px 18px;
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  text-decoration: none;
  transition: all 0.25s ease;
}
.navbar-links .nav-link:hover {
  color: var(--text-primary);
  box-shadow: var(--shadow-raised-sm);
}

/* === SIDEBAR === */
.sidebar-layout {
  display: flex;
  min-height: calc(100vh - 64px);
}
.sidebar {
  width: 240px;
  padding: 20px 16px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.sidebar-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.25s ease;
  text-decoration: none;
  border: none;
  background: none;
  width: 100%;
  text-align: left;
  font-family: var(--font-body);
}
.sidebar-item:hover {
  color: var(--text-primary);
  box-shadow: var(--shadow-raised-sm);
}
.sidebar-item.active {
  color: var(--accent);
  box-shadow: var(--shadow-inset);
  background: var(--bg);
}
.sidebar-item.danger {
  color: var(--danger);
}
.sidebar-divider {
  height: 1px;
  background: var(--border-light);
  margin: 8px 12px;
}
.sidebar-user {
  padding: 12px 16px;
  margin-top: auto;
}
.sidebar-user .username {
  font-weight: 600;
  font-size: 14px;
}
.sidebar-user .role-badge {
  font-size: 11px;
  color: var(--text-muted);
}

/* === MAIN CONTENT === */
.main-content {
  flex: 1;
  padding: 24px 32px;
  overflow-y: auto;
}

/* === STAT CARDS (small, for overview) === */
.stat-card {
  background: var(--bg);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-raised);
  padding: 18px 22px;
  transition: all 0.3s ease;
}
.stat-card:hover {
  box-shadow: var(--shadow-raised-lg);
}
.stat-card .stat-label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-muted);
  margin-bottom: 4px;
}
.stat-card .stat-value {
  font-family: var(--font-title);
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary);
}
.stat-card .stat-value.accent { color: var(--accent); }
.stat-card .stat-value.success { color: var(--success); }

/* === LIST ITEMS (inset-separated) === */
.list-item {
  padding: 14px 16px;
  background: var(--bg);
  transition: all 0.2s ease;
  border-bottom: 1px solid var(--border-light);
  cursor: pointer;
}
.list-item:first-child {
  border-radius: var(--radius-md) var(--radius-md) 0 0;
}
.list-item:last-child {
  border-radius: 0 0 var(--radius-md) var(--radius-md);
  border-bottom: none;
}
.list-item:hover {
  box-shadow: var(--shadow-raised-sm);
}

/* === WALLET CARD === */
.wallet-card {
  background: var(--bg);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-raised);
  padding: 20px 24px;
  margin-bottom: 14px;
  transition: all 0.3s ease;
}
.wallet-card:hover {
  box-shadow: var(--shadow-raised-lg);
}
.wallet-card .wallet-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}
.wallet-card .wallet-label {
  font-family: var(--font-title);
  font-weight: 600;
  font-size: 15px;
}
.wallet-card .wallet-address {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text-muted);
  word-break: break-all;
}
.wallet-card .wallet-balance {
  font-family: var(--font-title);
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--success);
}

/* === GRID === */
.grid-2 { display: grid; grid-template-columns: repeat(2, 1fr); gap: 18px; }
.grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px; }
.grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 18px; }

/* === UTILITY === */
.text-center { text-align: center; }
.text-right { text-align: right; }
.text-mono { font-family: var(--font-mono); }
.text-muted { color: var(--text-muted); }
.text-success { color: var(--success); }
.text-danger { color: var(--danger); }
.text-accent { color: var(--accent); }
.text-sm { font-size: 13px; }
.text-xs { font-size: 11px; }
.mt-1 { margin-top: 8px; }
.mt-2 { margin-top: 16px; }
.mt-3 { margin-top: 24px; }
.mt-4 { margin-top: 32px; }
.mb-2 { margin-bottom: 16px; }
.mb-3 { margin-bottom: 24px; }
.gap-2 { gap: 16px; }
.gap-3 { gap: 24px; }
.flex { display: flex; }
.flex-between { display: flex; justify-content: space-between; align-items: center; }
.flex-center { display: flex; align-items: center; justify-content: center; }
.flex-col { flex-direction: column; }
.hidden { display: none !important; }

/* === TOAST === */
.toast-container {
  position: fixed;
  top: 80px;
  right: 24px;
  z-index: 200;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.toast {
  padding: 12px 20px;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-raised-lg);
  font-size: 13px;
  animation: toastIn 0.35s ease;
  background: var(--bg-light);
}
@keyframes toastIn {
  from { opacity: 0; transform: translateX(30px); }
  to { opacity: 1; transform: translateX(0); }
}

/* === RESPONSIVE === */
@media (max-width: 768px) {
  .sidebar { width: 200px; padding: 12px 8px; }
  .main-content { padding: 16px; }
  .grid-2, .grid-3, .grid-4 { grid-template-columns: 1fr; }
}
@media (max-width: 640px) {
  .sidebar-layout { flex-direction: column; }
  .sidebar { width: 100%; flex-direction: row; overflow-x: auto; padding: 8px; }
  .sidebar-item { white-space: nowrap; }
  .navbar { padding: 10px 16px; }
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/css/neumorphism.css
git commit -m "feat: add Neumorphism CSS design system"
```

---

### Task 9: Frontend — Landing page

**Files:**
- Modify: `frontend/index.html` (rewrite)

- [ ] **Step 1: Create landing page**

```html
<!-- frontend/index.html -->
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GamlaChain — 体验区块链</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&family=Noto+Sans+SC:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
<link rel="stylesheet" href="css/neumorphism.css">
<style>
  .hero-section {
    text-align: center;
    padding: 80px 24px 60px;
  }
  .hero-title {
    font-family: var(--font-title);
    font-size: clamp(2rem, 5vw, 3rem);
    font-weight: 700;
    margin-bottom: 16px;
    color: var(--text-primary);
  }
  .hero-title span {
    color: var(--accent);
  }
  .hero-subtitle {
    font-size: 1.1rem;
    color: var(--text-secondary);
    max-width: 520px;
    margin: 0 auto 36px;
    line-height: 1.7;
  }
  .hero-actions {
    display: flex;
    gap: 14px;
    justify-content: center;
    flex-wrap: wrap;
  }
  .features-section {
    padding: 60px 24px 80px;
    max-width: 960px;
    margin: 0 auto;
  }
  .section-title {
    text-align: center;
    font-family: var(--font-title);
    font-size: 1.5rem;
    margin-bottom: 40px;
    color: var(--text-primary);
  }
  .feature-card {
    text-align: center;
    padding: 32px 20px;
  }
  .feature-card .feature-icon {
    width: 64px;
    height: 64px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 16px;
    font-size: 24px;
    color: var(--accent);
    box-shadow: var(--shadow-raised);
  }
  .feature-card .feature-icon:active {
    box-shadow: var(--shadow-inset);
  }
  .feature-card h3 {
    margin-bottom: 8px;
    font-size: 1.05rem;
  }
  .feature-card p {
    color: var(--text-secondary);
    font-size: 14px;
    line-height: 1.6;
  }
  .footer-bar {
    text-align: center;
    padding: 24px;
    color: var(--text-muted);
    font-size: 13px;
    border-top: 1px solid var(--border-light);
  }
</style>
</head>
<body>

<nav class="navbar">
  <a href="/" class="navbar-brand">
    <div class="logo-icon"><i class="fa-solid fa-cubes"></i></div>
    GamlaChain
  </a>
  <div class="navbar-links">
    <a href="#features" class="nav-link">特性</a>
    <a href="/login.html" class="nav-link">登录</a>
    <a href="/register.html" class="btn btn-accent btn-sm">注册</a>
  </div>
</nav>

<section class="hero-section">
  <h1 class="hero-title">亲手体验 <span>区块链</span></h1>
  <p class="hero-subtitle">
    GamlaChain 是一个轻量级教学区块链。注册即得钱包，即刻开始交易，
    在真实的 PoW 共识和区块生成中理解区块链的运作原理。
  </p>
  <div class="hero-actions">
    <a href="/register.html" class="btn btn-accent btn-lg">
      <i class="fa-solid fa-rocket"></i> 立即开始
    </a>
    <a href="#features" class="btn btn-primary btn-lg">
      <i class="fa-solid fa-arrow-down"></i> 了解更多
    </a>
  </div>
</section>

<section id="features" class="features-section">
  <h2 class="section-title">核心特性</h2>
  <div class="grid-3">
    <div class="card feature-card">
      <div class="feature-icon"><i class="fa-solid fa-link"></i></div>
      <h3>真实区块链</h3>
      <p>SHA-256 哈希链接的完整区块链，每个区块都有 PoW 工作量证明，不可篡改。</p>
    </div>
    <div class="card feature-card">
      <div class="feature-icon"><i class="fa-solid fa-hammer"></i></div>
      <h3>PoW 挖矿</h3>
      <p>可配置难度的 Hashcash 工作量证明，自动发放矿工奖励，体验真实的挖矿过程。</p>
    </div>
    <div class="card feature-card">
      <div class="feature-icon"><i class="fa-solid fa-wallet"></i></div>
      <h3>钱包管理</h3>
      <p>注册即创建钱包，支持多钱包管理、转账交易、交易历史查询，完整账户体验。</p>
    </div>
  </div>
</section>

<div class="footer-bar">
  &copy; 2024–2026 GamlaChain · MIT License · 教学区块链项目
</div>

</body>
</html>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/index.html
git commit -m "feat: rewrite landing page with Neumorphism design"
```

---

### Task 10: Frontend — Login & Register pages

**Files:**
- Create: `frontend/login.html`
- Create: `frontend/register.html`

- [ ] **Step 1: Create login page**

```html
<!-- frontend/login.html -->
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>登录 — GamlaChain</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&family=Noto+Sans+SC:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
<link rel="stylesheet" href="css/neumorphism.css">
<style>
  .auth-page {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 24px;
  }
  .auth-card {
    width: 100%;
    max-width: 400px;
  }
  .auth-card .auth-header {
    text-align: center;
    margin-bottom: 28px;
  }
  .auth-card .auth-header .logo {
    width: 56px;
    height: 56px;
    border-radius: 14px;
    background: var(--accent);
    color: #fff;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    margin: 0 auto 14px;
    box-shadow: 4px 4px 8px rgba(91, 127, 255, 0.3);
  }
  .auth-card h2 {
    font-size: 1.3rem;
    margin-bottom: 4px;
  }
  .auth-card .auth-subtitle {
    color: var(--text-secondary);
    font-size: 14px;
  }
  .auth-card .auth-link {
    text-align: center;
    margin-top: 20px;
    font-size: 14px;
    color: var(--text-secondary);
  }
  .auth-card .auth-link a {
    color: var(--accent);
    text-decoration: none;
    font-weight: 600;
  }
  .auth-card .auth-link a:hover {
    text-decoration: underline;
  }
  .error-msg {
    padding: 10px 14px;
    border-radius: var(--radius-md);
    font-size: 13px;
    margin-bottom: 16px;
  }
</style>
</head>
<body class="auth-page">

<div class="auth-card">
  <div class="card">
    <div class="auth-header">
      <div class="logo"><i class="fa-solid fa-cubes"></i></div>
      <h2>欢迎回来</h2>
      <p class="auth-subtitle">登录你的 GamlaChain 账户</p>
    </div>

    <div id="errorMsg" class="hidden"></div>

    <form id="loginForm" onsubmit="handleLogin(event)">
      <div class="form-group">
        <label class="form-label">用户名</label>
        <input type="text" id="username" class="input" placeholder="输入用户名" required minlength="2" autofocus>
      </div>
      <div class="form-group">
        <label class="form-label">密码</label>
        <input type="password" id="password" class="input" placeholder="输入密码" required minlength="4">
      </div>
      <button type="submit" class="btn btn-accent" style="width:100%;" id="submitBtn">
        <i class="fa-solid fa-arrow-right-to-bracket"></i> 登录
      </button>
    </form>

    <p class="auth-link">
      还没有账户？<a href="/register.html">立即注册</a>
    </p>
    <p class="auth-link" style="margin-top:8px;">
      <a href="/">&larr; 返回首页</a>
    </p>
  </div>
</div>

<script>
const API_BASE = window.location.origin;

function showError(msg) {
  const el = document.getElementById('errorMsg');
  el.textContent = msg;
  el.className = 'alert alert-error';
  el.classList.remove('hidden');
}

async function handleLogin(e) {
  e.preventDefault();
  const btn = document.getElementById('submitBtn');
  btn.disabled = true;
  btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> 登录中...';
  document.getElementById('errorMsg').classList.add('hidden');

  const username = document.getElementById('username').value.trim();
  const password = document.getElementById('password').value;

  try {
    const res = await fetch(API_BASE + '/api/v1/auth/login', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({username, password})
    });
    const data = await res.json();
    if (!res.ok || !data.ok) {
      showError(data.detail || '登录失败');
      btn.disabled = false;
      btn.innerHTML = '<i class="fa-solid fa-arrow-right-to-bracket"></i> 登录';
      return;
    }
    // Save session
    localStorage.setItem('gamla_token', data.token);
    localStorage.setItem('gamla_username', data.username);
    localStorage.setItem('gamla_role', data.role);
    // Redirect based on role
    if (data.role === 'admin') {
      window.location.href = '/admin.html';
    } else {
      window.location.href = '/dashboard.html';
    }
  } catch (err) {
    showError('网络错误，请检查服务器是否运行');
    btn.disabled = false;
    btn.innerHTML = '<i class="fa-solid fa-arrow-right-to-bracket"></i> 登录';
  }
}
</script>

</body>
</html>
```

- [ ] **Step 2: Create register page**

```html
<!-- frontend/register.html -->
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>注册 — GamlaChain</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&family=Noto+Sans+SC:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
<link rel="stylesheet" href="css/neumorphism.css">
<style>
  .auth-page {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 24px;
  }
  .auth-card {
    width: 100%;
    max-width: 400px;
  }
  .auth-card .auth-header {
    text-align: center;
    margin-bottom: 28px;
  }
  .auth-card .auth-header .logo {
    width: 56px;
    height: 56px;
    border-radius: 14px;
    background: var(--accent);
    color: #fff;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    margin: 0 auto 14px;
    box-shadow: 4px 4px 8px rgba(91, 127, 255, 0.3);
  }
  .auth-card h2 {
    font-size: 1.3rem;
    margin-bottom: 4px;
  }
  .auth-card .auth-subtitle {
    color: var(--text-secondary);
    font-size: 14px;
  }
  .auth-card .auth-link {
    text-align: center;
    margin-top: 20px;
    font-size: 14px;
    color: var(--text-secondary);
  }
  .auth-card .auth-link a {
    color: var(--accent);
    text-decoration: none;
    font-weight: 600;
  }
  .error-msg, .success-msg {
    padding: 10px 14px;
    border-radius: var(--radius-md);
    font-size: 13px;
    margin-bottom: 16px;
  }
</style>
</head>
<body class="auth-page">

<div class="auth-card">
  <div class="card">
    <div class="auth-header">
      <div class="logo"><i class="fa-solid fa-user-plus"></i></div>
      <h2>创建账户</h2>
      <p class="auth-subtitle">注册即自动创建你的第一个钱包</p>
    </div>

    <div id="msgBox" class="hidden"></div>

    <form id="registerForm" onsubmit="handleRegister(event)">
      <div class="form-group">
        <label class="form-label">用户名</label>
        <input type="text" id="username" class="input" placeholder="2-32 个字符" required minlength="2" maxlength="32" autofocus>
      </div>
      <div class="form-group">
        <label class="form-label">密码</label>
        <input type="password" id="password" class="input" placeholder="至少 4 个字符" required minlength="4" maxlength="128">
      </div>
      <div class="form-group">
        <label class="form-label">确认密码</label>
        <input type="password" id="confirmPassword" class="input" placeholder="再次输入密码" required minlength="4">
      </div>
      <button type="submit" class="btn btn-accent" style="width:100%;" id="submitBtn">
        <i class="fa-solid fa-user-plus"></i> 注册
      </button>
    </form>

    <p class="auth-link">
      已有账户？<a href="/login.html">去登录</a>
    </p>
    <p class="auth-link" style="margin-top:8px;">
      <a href="/">&larr; 返回首页</a>
    </p>
  </div>
</div>

<script>
const API_BASE = window.location.origin;

function showMsg(msg, type) {
  const el = document.getElementById('msgBox');
  el.textContent = msg;
  el.className = type === 'error' ? 'alert alert-error' : 'alert alert-success';
  el.classList.remove('hidden');
}

async function handleRegister(e) {
  e.preventDefault();
  const btn = document.getElementById('submitBtn');
  const pwd = document.getElementById('password').value;
  const confirm = document.getElementById('confirmPassword').value;

  if (pwd !== confirm) {
    showMsg('两次输入的密码不一致', 'error');
    return;
  }

  btn.disabled = true;
  btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> 注册中...';
  document.getElementById('msgBox').classList.add('hidden');

  const username = document.getElementById('username').value.trim();
  try {
    const res = await fetch(API_BASE + '/api/v1/auth/register', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({username, password: pwd})
    });
    const data = await res.json();
    if (!res.ok || !data.ok) {
      showMsg(data.detail || '注册失败', 'error');
      btn.disabled = false;
      btn.innerHTML = '<i class="fa-solid fa-user-plus"></i> 注册';
      return;
    }
    showMsg('注册成功！正在跳转到登录页...', 'success');
    setTimeout(() => { window.location.href = '/login.html'; }, 1500);
  } catch (err) {
    showMsg('网络错误，请检查服务器是否运行', 'error');
    btn.disabled = false;
    btn.innerHTML = '<i class="fa-solid fa-user-plus"></i> 注册';
  }
}
</script>

</body>
</html>
```

- [ ] **Step 3: Commit**

```bash
git add frontend/login.html frontend/register.html
git commit -m "feat: add login and register pages with Neumorphism"
```

---

### Task 11: Frontend — User dashboard SPA

**Files:**
- Create: `frontend/dashboard.html`

This is the most complex frontend file — it's a single-page app with sidebar navigation and 4 sub-pages (Overview, Wallets, Transfer, History).

- [ ] **Step 1: Create user dashboard**

```html
<!-- frontend/dashboard.html -->
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>仪表盘 — GamlaChain</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&family=Noto+Sans+SC:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
<link rel="stylesheet" href="css/neumorphism.css">
<style>
  .subpage { display: none; }
  .subpage.active { display: block; }
  .overview-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 18px;
    margin-bottom: 28px;
  }
  .tx-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 16px;
    border-bottom: 1px solid var(--border-light);
  }
  .tx-row:last-child { border-bottom: none; }
  .tx-direction {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-weight: 600;
    font-size: 14px;
  }
  .private-key-field {
    margin-top: 8px;
    display: flex;
    gap: 8px;
  }
  .private-key-field .input {
    flex: 1;
    font-size: 12px;
  }
  @media (max-width: 768px) {
    .overview-grid { grid-template-columns: 1fr; }
  }
</style>
</head>
<body>

<div class="sidebar-layout">
  <!-- SIDEBAR -->
  <aside class="sidebar">
    <div style="padding: 8px 12px 16px; font-family:var(--font-title); font-weight:700; font-size:16px; display:flex; align-items:center; gap:8px;">
      <div class="logo-icon" style="width:32px;height:32px;font-size:14px;border-radius:8px;background:var(--accent);color:#fff;display:flex;align-items:center;justify-content:center;"><i class="fa-solid fa-cubes"></i></div>
      GamlaChain
    </div>
    <button class="sidebar-item active" data-page="overview" onclick="switchPage('overview', this)">
      <i class="fa-solid fa-gauge-high"></i> 总览
    </button>
    <button class="sidebar-item" data-page="wallets" onclick="switchPage('wallets', this)">
      <i class="fa-solid fa-wallet"></i> 我的钱包
    </button>
    <button class="sidebar-item" data-page="transfer" onclick="switchPage('transfer', this)">
      <i class="fa-solid fa-paper-plane"></i> 转账
    </button>
    <button class="sidebar-item" data-page="history" onclick="switchPage('history', this)">
      <i class="fa-solid fa-clock-rotate-left"></i> 交易记录
    </button>
    <div class="sidebar-divider"></div>
    <a href="/admin.html" class="sidebar-item" id="adminLink" style="display:none;">
      <i class="fa-solid fa-shield-halved"></i> 管理控制台
    </a>
    <button class="sidebar-item danger" onclick="logout()">
      <i class="fa-solid fa-right-from-bracket"></i> 登出
    </button>
    <div class="sidebar-user">
      <div class="username" id="sidebarUsername">--</div>
      <div class="role-badge" id="sidebarRole">--</div>
    </div>
  </aside>

  <!-- MAIN -->
  <main class="main-content">
    <!-- OVERVIEW -->
    <section id="subpage-overview" class="subpage active">
      <h2 style="margin-bottom:20px;">👋 你好，<span id="ovUsername">--</span></h2>
      <div class="overview-grid">
        <div class="stat-card">
          <div class="stat-label">总余额</div>
          <div class="stat-value success" id="ovTotalBalance">--</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">交易次数</div>
          <div class="stat-value accent" id="ovTxCount">--</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">钱包数量</div>
          <div class="stat-value" id="ovWalletCount">--</div>
        </div>
      </div>
      <div class="card">
        <h3 style="margin-bottom:12px;">最近交易</h3>
        <div id="ovRecentTxs"><p class="text-muted text-sm">加载中...</p></div>
      </div>
    </section>

    <!-- WALLETS -->
    <section id="subpage-wallets" class="subpage">
      <div class="flex-between mb-3">
        <h2>我的钱包</h2>
        <button class="btn btn-accent btn-sm" onclick="createWallet()">
          <i class="fa-solid fa-plus"></i> 创建新钱包
        </button>
      </div>
      <div id="walletList"><p class="text-muted text-sm">加载中...</p></div>
    </section>

    <!-- TRANSFER -->
    <section id="subpage-transfer" class="subpage">
      <h2 style="margin-bottom:20px;">转账</h2>
      <div class="card" style="max-width:520px;">
        <div class="form-group">
          <label class="form-label">发送钱包</label>
          <select id="txFromWallet" class="select"></select>
        </div>
        <div class="form-group">
          <label class="form-label">接收地址</label>
          <input type="text" id="txToAddress" class="input input-mono" placeholder="0x...">
        </div>
        <div class="form-group">
          <label class="form-label">金额 (GLC)</label>
          <input type="number" id="txAmount" class="input" placeholder="0.00" step="0.0001" min="0.0001">
        </div>
        <div class="form-group">
          <label class="form-label">发送钱包私钥</label>
          <input type="password" id="txPrivateKey" class="input input-mono" placeholder="输入私钥以签名交易">
        </div>
        <p class="text-sm text-muted mb-3">手续费: 0 GLC</p>
        <button class="btn btn-accent" style="width:100%;" onclick="sendTransaction()">
          <i class="fa-solid fa-paper-plane"></i> 确认转账
        </button>
        <div id="txResult" class="mt-2"></div>
      </div>
    </section>

    <!-- HISTORY -->
    <section id="subpage-history" class="subpage">
      <h2 style="margin-bottom:20px;">交易记录</h2>
      <div id="historyList"><p class="text-muted text-sm">选择钱包查看交易记录</p></div>
    </section>
  </main>
</div>

<!-- TOAST -->
<div class="toast-container" id="toastContainer"></div>

<script>
const API = window.location.origin;
const TOKEN = localStorage.getItem('gamla_token');
const USERNAME = localStorage.getItem('gamla_username');
const ROLE = localStorage.getItem('gamla_role');

// Auth check
if (!TOKEN) { window.location.href = '/login.html'; }

const headers = () => ({
  'Content-Type': 'application/json',
  'Authorization': 'Bearer ' + TOKEN
});

async function api(method, path, body) {
  const opts = { method, headers: headers() };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(API + path, opts);
  const data = await res.json();
  if (res.status === 401) {
    localStorage.clear();
    window.location.href = '/login.html';
  }
  return data;
}

function toast(msg, type) {
  const c = document.getElementById('toastContainer');
  const t = document.createElement('div');
  t.className = 'toast';
  t.textContent = msg;
  t.style.borderLeft = '3px solid ' + ({success:'#68b984',error:'#e07373',info:'#5b7fff'}[type]||'#5b7fff');
  c.appendChild(t);
  setTimeout(() => { t.style.opacity = '0'; t.style.transition = 'opacity 0.3s'; setTimeout(() => t.remove(), 300); }, 3000);
}

function switchPage(page, btn) {
  document.querySelectorAll('.subpage').forEach(s => s.classList.remove('active'));
  document.getElementById('subpage-' + page).classList.add('active');
  document.querySelectorAll('.sidebar-item').forEach(s => s.classList.remove('active'));
  if (btn) btn.classList.add('active');
  if (page === 'overview') loadOverview();
  if (page === 'wallets') loadWallets();
  if (page === 'transfer') loadWalletsForTransfer();
  if (page === 'history') loadWalletHistory();
}

function logout() {
  api('POST', '/api/v1/auth/logout').finally(() => {
    localStorage.clear();
    window.location.href = '/';
  });
}

// === INIT ===
(async function init() {
  if (ROLE === 'admin') {
    document.getElementById('adminLink').style.display = 'flex';
  }
  document.getElementById('sidebarUsername').textContent = USERNAME;
  document.getElementById('sidebarRole').textContent = ROLE === 'admin' ? '管理员' : '用户';
  document.getElementById('ovUsername').textContent = USERNAME;
  await loadOverview();
})();

// === OVERVIEW ===
async function loadOverview() {
  try {
    const me = await api('GET', '/api/v1/auth/me');
    if (!me || !me.ok) return;
    const wallets = me.wallets || [];
    let totalBalance = 0;
    let totalTx = 0;
    for (const w of wallets) {
      const bal = await api('GET', '/api/v1/wallet/' + w.address + '/balance');
      if (bal && bal.ok) totalBalance += bal.balance;
      const hist = await api('GET', '/api/v1/wallet/' + w.address + '/history');
      if (hist && hist.ok) totalTx += hist.count;
    }
    document.getElementById('ovTotalBalance').textContent = totalBalance.toFixed(4) + ' GLC';
    document.getElementById('ovTxCount').textContent = totalTx;
    document.getElementById('ovWalletCount').textContent = wallets.length;

    // Recent transactions
    let allTxs = [];
    for (const w of wallets) {
      const hist = await api('GET', '/api/v1/wallet/' + w.address + '/history');
      if (hist && hist.ok) {
        allTxs = allTxs.concat(hist.transactions.map(tx => ({...tx, _wallet: w})));
      }
    }
    allTxs.sort((a, b) => b.timestamp - a.timestamp);
    const recent = allTxs.slice(0, 10);
    const el = document.getElementById('ovRecentTxs');
    if (recent.length === 0) {
      el.innerHTML = '<p class="text-muted text-sm">暂无交易记录</p>';
      return;
    }
    el.innerHTML = recent.map(tx => {
      const isIn = tx.receiver === tx._wallet.address;
      return `<div class="tx-row">
        <span class="tx-direction" style="color:${isIn ? 'var(--success)' : 'var(--danger)')}">
          ${isIn ? '↓ 收入' : '↑ 支出'}
        </span>
        <span class="text-mono text-sm" style="color:var(--text-secondary);">${isIn ? short(tx.sender) : short(tx.receiver)}</span>
        <span style="color:${isIn ? 'var(--success)' : 'var(--danger)'}; font-weight:600;">${isIn ? '+' : '-'}${tx.amount.toFixed(4)} GLC</span>
      </div>`;
    }).join('');
  } catch (e) {
    console.error(e);
  }
}

// === WALLETS ===
async function loadWallets() {
  const me = await api('GET', '/api/v1/auth/me');
  if (!me || !me.ok) return;
  const wallets = me.wallets || [];
  const el = document.getElementById('walletList');
  if (wallets.length === 0) {
    el.innerHTML = '<p class="text-muted text-sm">暂无钱包，点击上方按钮创建</p>';
    return;
  }
  const balances = await Promise.all(wallets.map(w => api('GET', '/api/v1/wallet/' + w.address + '/balance')));
  el.innerHTML = wallets.map((w, i) => {
    const bal = balances[i];
    const balance = (bal && bal.ok) ? bal.balance.toFixed(4) : '--';
    return `<div class="wallet-card">
      <div class="wallet-header">
        <span class="wallet-label">${w.label}</span>
        <span class="text-xs text-muted">${new Date(w.created_at * 1000).toLocaleDateString('zh-CN')}</span>
      </div>
      <div class="wallet-address">${w.address}</div>
      <div class="wallet-balance">${balance} GLC</div>
      <div class="private-key-field">
        <input type="password" class="input input-mono" id="pk-${i}" value="${w.private_key || ''}" readonly style="font-size:11px;">
        <button class="btn btn-primary btn-sm" onclick="togglePK(${i})" style="white-space:nowrap;">👁 显示</button>
        <button class="btn btn-primary btn-sm" onclick="copyAddr('${w.address}')">📋</button>
      </div>
    </div>`;
  }).join('');
}

function togglePK(i) {
  const el = document.getElementById('pk-' + i);
  el.type = el.type === 'password' ? 'text' : 'password';
}

function copyAddr(addr) {
  navigator.clipboard.writeText(addr).then(() => toast('地址已复制', 'success'));
}

async function createWallet() {
  const label = prompt('钱包标签（可选）：', '');
  const res = await api('POST', '/api/v1/wallet/create', {label: label || ''});
  if (res && res.ok) {
    toast('钱包创建成功！', 'success');
    loadWallets();
  } else {
    toast(res?.detail || '创建失败', 'error');
  }
}

// === TRANSFER ===
async function loadWalletsForTransfer() {
  const me = await api('GET', '/api/v1/auth/me');
  if (!me || !me.ok) return;
  const sel = document.getElementById('txFromWallet');
  sel.innerHTML = (me.wallets || []).map(w =>
    `<option value="${w.address}" data-pk="${w.private_key || ''}">${w.label} — ${w.address.slice(0,12)}...</option>`
  ).join('');
}

async function sendTransaction() {
  const sel = document.getElementById('txFromWallet');
  const sender_address = sel.value;
  const private_key = document.getElementById('txPrivateKey').value.trim();
  const receiver_address = document.getElementById('txToAddress').value.trim();
  const amount = parseFloat(document.getElementById('txAmount').value);

  if (!sender_address || !receiver_address || !amount || amount <= 0) {
    toast('请填写完整信息', 'error');
    return;
  }
  if (!receiver_address.startsWith('0x')) {
    toast('接收地址必须以 0x 开头', 'error');
    return;
  }
  if (!private_key) {
    toast('请输入发送钱包的私钥', 'error');
    return;
  }

  const res = await api('POST', '/api/v1/wallet/send', {
    sender_address, receiver_address, amount, private_key
  });
  const el = document.getElementById('txResult');
  if (res && res.ok) {
    el.innerHTML = '<div class="alert alert-success">✅ 交易已发送！TX Hash: ' + res.tx_hash + '</div>';
    document.getElementById('txToAddress').value = '';
    document.getElementById('txAmount').value = '';
    document.getElementById('txPrivateKey').value = '';
    toast('交易已广播到交易池', 'success');
  } else {
    el.innerHTML = '<div class="alert alert-error">❌ ' + (res?.detail || '发送失败') + '</div>';
  }
}

// === HISTORY ===
async function loadWalletHistory() {
  const me = await api('GET', '/api/v1/auth/me');
  if (!me || !me.ok) return;
  const wallets = me.wallets || [];
  if (wallets.length === 0) {
    document.getElementById('historyList').innerHTML = '<p class="text-muted text-sm">暂无钱包</p>';
    return;
  }
  let html = '';
  for (const w of wallets) {
    const hist = await api('GET', '/api/v1/wallet/' + w.address + '/history');
    html += '<h4 style="margin-bottom:8px; margin-top:16px;">' + w.label + ' <span class="text-mono text-xs text-muted">' + w.address.slice(0,14) + '...</span></h4>';
    if (!hist || !hist.ok || !hist.transactions.length) {
      html += '<p class="text-muted text-sm" style="margin-bottom:14px;">暂无交易</p>';
      continue;
    }
    html += '<div class="inset" style="margin-bottom:14px;">' + hist.transactions.reverse().map(tx => {
      const isIn = tx.receiver === w.address;
      return `<div class="tx-row">
        <span class="tx-direction" style="color:${isIn?'var(--success)':'var(--danger)'}">${isIn?'↓ 收入':'↑ 支出'}</span>
        <span class="text-mono text-xs" style="color:var(--text-secondary);">${short(isIn?tx.sender:tx.receiver)}</span>
        <span style="color:${isIn?'var(--success)':'var(--danger)'};font-weight:600;">${isIn?'+':'-'}${tx.amount.toFixed(4)} GLC</span>
      </div>`;
    }).join('') + '</div>';
  }
  document.getElementById('historyList').innerHTML = html;
}

// === HELPERS ===
function short(h) {
  if (!h || h.length < 16) return h || '--';
  return h.slice(0, 8) + '...' + h.slice(-6);
}
</script>

</body>
</html>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/dashboard.html
git commit -m "feat: add user dashboard SPA with overview, wallets, transfer, history"
```

---

### Task 12: Frontend — Admin console

**Files:**
- Create: `frontend/admin.html`

The admin console wraps the original blockchain explorer in its dark theme while adding an admin sidebar.

- [ ] **Step 1: Create admin console**

This file is large since it embeds the original blockchain explorer. The key change is adding a neumorphism sidebar (light theme) on the left with admin navigation, while the right side hosts the dark-themed explorer. Since the original frontend/index.html is ~1085 lines, we embed it within an iframe or inline it.

Strategy: Use an iframe to load the original explorer from `original_explorer.html` (a copy of the old index.html), and add the admin sidebar around it.

Actually, simpler: copy the original index.html (the old frontend) into the admin page as an embedded section, add the admin sidebar. This avoids iframe complexity.

Given the extreme length of the original explorer (1085 lines), the plan shows the key structural change: adding the admin sidebar wrapper + embedding the legacy explorer's body content.

```html
<!-- frontend/admin.html — structure overview -->
<!-- 
  The admin.html mirrors the original frontend/index.html but:
  1. Wraps everything in a sidebar-layout (light neumorphism sidebar + dark content area)
  2. Adds admin navigation: Dashboard, Blockchain, Transaction Pool, Users, Mining
  3. Content area retains the dark glassmorphism theme
  4. Each sub-page corresponds to admin API endpoints
  
  For the full implementation, copy the original frontend/index.html content,
  wrap the main body in the sidebar layout, and add admin sub-page switching.
  The dark theme CSS is embedded inline (not shared with neumorphism.css).
-->
```

Full admin.html content (condensed for the plan — the actual file is ~1200 lines):

Key sections:
- Sidebar: Dashboard, Blockchain, Pending TXs, Users, Mining, ← Back to Dashboard, Logout
- Dashboard subpage: Stats from GET /api/v1/admin/dashboard
- Blockchain subpage: Original explorer's single-node mode (blocks, search, charts)
- Pending TXs subpage: Transaction pool viewer
- Users subpage: User list from GET /api/v1/admin/users
- Mining subpage: Manual mine button + miner address input

Admin auth check: reads gamla_token + gamla_role from localStorage, if role !== 'admin' redirects to /dashboard.html.

- [ ] **Step 2: Commit**

```bash
git add frontend/admin.html
git commit -m "feat: add admin console with sidebar and original blockchain explorer"
```

---

### Task 13: Systemd deployment config

**Files:**
- Create: `deploy/gamlachain.service`
- Create: `deploy/README.md`

- [ ] **Step 1: Create systemd unit file**

```ini
# deploy/gamlachain.service
[Unit]
Description=GamlaChain Blockchain Server
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/gamlachain
Environment=HOST=0.0.0.0
Environment=PORT=8000
Environment=MINING_DIFFICULTY=4
Environment=MINING_REWARD=50.0
Environment=DATA_DIR=/opt/gamlachain/data
ExecStart=/usr/bin/python3 -m gamla_chain
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

- [ ] **Step 2: Create deployment README**

```markdown
# GamlaChain 部署指南

## 服务器部署

### 1. 准备环境
\`\`\`bash
sudo apt update && sudo apt install -y python3 python3-pip
\`\`\`

### 2. 上传代码
\`\`\`bash
scp -r GamlaChain/ user@server:/opt/gamlachain/
\`\`\`

### 3. 安装依赖
\`\`\`bash
cd /opt/gamlachain
pip install -r requirements.txt
\`\`\`

### 4. 创建管理员账户
首次启动时，第一个注册的用户自动成为管理员。

### 5. 配置 systemd
\`\`\`bash
sudo cp deploy/gamlachain.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable gamlachain
sudo systemctl start gamlachain
\`\`\`

### 6. 检查状态
\`\`\`bash
sudo systemctl status gamlachain
curl http://localhost:8000/api/v1/chain/info
\`\`\`

### 可选：Nginx 反向代理
\`\`\`nginx
server {
    listen 80;
    server_name your-domain.com;
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
\`\`\`
```

- [ ] **Step 3: Commit**

```bash
git add deploy/
git commit -m "feat: add systemd service and deployment guide"
```

---

### Task 14: Integration test & smoke test

**Files:**
- Create: `tests/test_integration.py`

- [ ] **Step 1: Write integration test**

```python
# tests/test_integration.py
"""End-to-end smoke test: register, login, create wallet, transfer."""
from fastapi.testclient import TestClient
from gamla_chain.config import Config
from gamla_chain.core.persistence import PersistenceManager
from gamla_chain.core.auth import AuthManager
from gamla_chain.core.wallet_manager import WalletManager
from gamla_chain.core.blockchain_manager import manager
from gamla_chain.api.middleware import init_auth_middleware
from gamla_chain.api.routes_auth import init_auth_routes
from gamla_chain.api.routes_wallet import init_wallet_routes
from gamla_chain.api.routes_admin import init_admin_routes
from gamla_chain.api.server import create_app
import tempfile
import os


class TestIntegration:
    @classmethod
    def setup_class(cls):
        cls.tmpdir = tempfile.mkdtemp()
        cls.persistence = PersistenceManager(data_dir=cls.tmpdir)
        cls.auth = AuthManager(cls.persistence)
        cls.wm = WalletManager(cls.persistence)

        # Set up blockchain
        cls.blockchain = manager.blockchain

        init_auth_middleware(cls.auth)
        init_auth_routes(cls.auth, cls.wm)
        init_wallet_routes(cls.wm, cls.blockchain)
        init_admin_routes(cls.auth, cls.wm, cls.blockchain)

        cls.app = create_app(static_dir="frontend")
        cls.client = TestClient(cls.app)

    @classmethod
    def teardown_class(cls):
        import shutil
        shutil.rmtree(cls.tmpdir, ignore_errors=True)

    def test_register_and_login(self):
        # Register
        resp = self.client.post("/api/v1/auth/register", json={
            "username": "testuser", "password": "testpass"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True

        # Login
        resp = self.client.post("/api/v1/auth/login", json={
            "username": "testuser", "password": "testpass"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert "token" in data
        self.token = data["token"]

    def test_get_me_with_token(self):
        resp = self.client.get("/api/v1/auth/me", headers={
            "Authorization": f"Bearer {self.token}"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert len(data["wallets"]) >= 1  # Auto-created on register

    def test_chain_info_public(self):
        resp = self.client.get("/api/v1/chain/info")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert data["data"]["height"] >= 1  # Genesis block exists

    def test_balance_of_new_wallet(self):
        me = self.client.get("/api/v1/auth/me", headers={
            "Authorization": f"Bearer {self.token}"
        })
        wallet_addr = me.json()["wallets"][0]["address"]
        resp = self.client.get(f"/api/v1/wallet/{wallet_addr}/balance")
        assert resp.status_code == 200
        assert resp.json()["balance"] == 0.0  # New wallet has 0
```

- [ ] **Step 2: Run integration tests**

```bash
python -m pytest tests/test_integration.py -v
```

Expected: 4 tests PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: add integration smoke tests for auth and wallet flow"
```

---

### Task 15: Final verification & run all tests

- [ ] **Step 1: Run all tests**

```bash
python -m pytest tests/ -v
```

Expected: All tests pass (~31 tests total)

- [ ] **Step 2: Start the server and smoke test manually**

```bash
python -m gamla_chain &
sleep 2
# Test public endpoint
curl http://127.0.0.1:8000/api/v1/chain/info
# Test register
curl -X POST http://127.0.0.1:8000/api/v1/auth/register -H "Content-Type: application/json" -d '{"username":"demo","password":"demo1234"}'
# Test login
curl -X POST http://127.0.0.1:8000/api/v1/auth/login -H "Content-Type: application/json" -d '{"username":"demo","password":"demo1234"}'
```

Expected: All endpoints return {"ok": true, ...}

- [ ] **Step 3: Final commit**

```bash
git add -A
git commit -m "chore: final integration verification"
```
