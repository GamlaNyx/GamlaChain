"""Simple in-memory rate limiter for FastAPI endpoints."""
import time
import threading
from collections import defaultdict
from fastapi import Request, HTTPException


class RateLimiter:
    """Token-bucket-style rate limiter keyed by client IP."""

    def __init__(self, requests: int = 5, window_seconds: int = 60):
        self.requests = requests
        self.window = window_seconds
        self._hits: dict[str, list[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def _clean(self, ip: str, now: float) -> None:
        cutoff = now - self.window
        self._hits[ip] = [t for t in self._hits[ip] if t > cutoff]

    def is_allowed(self, ip: str) -> bool:
        now = time.time()
        with self._lock:
            self._clean(ip, now)
            if len(self._hits[ip]) >= self.requests:
                return False
            self._hits[ip].append(now)
            return True


# Pre-built limiters
login_limiter = RateLimiter(requests=10, window_seconds=60)   # 10 login attempts/min
register_limiter = RateLimiter(requests=5, window_seconds=60) # 5 registrations/min
faucet_limiter = RateLimiter(requests=3, window_seconds=60)   # already limited by user quota, add IP limit


def get_client_ip(request: Request) -> str:
    """Extract client IP, respecting X-Forwarded-For proxy header."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


async def check_rate_limit(request: Request, limiter: RateLimiter, action: str):
    """FastAPI dependency: raise 429 if rate limit exceeded."""
    ip = get_client_ip(request)
    if not limiter.is_allowed(ip):
        raise HTTPException(
            status_code=429,
            detail=f"Too many {action} attempts. Please wait and try again.",
        )
