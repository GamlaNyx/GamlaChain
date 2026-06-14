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
        self.sessions.pop(token, None)
        self._save_sessions()

    def get_user_by_token(self, token: str) -> User | None:
        session = self.sessions.get(token)
        if session is None:
            return None
        if session.expires_at < time.time():
            self.sessions.pop(token, None)
            self._save_sessions()
            return None
        for user in self.users.values():
            if user.id == session.user_id:
                return user
        return None
