from fastapi import Header, HTTPException
from gamla_chain.core.auth import User

_auth_manager = None

def init_auth_middleware(auth_manager):
    global _auth_manager
    _auth_manager = auth_manager

def _get_token(authorization: str | None = Header(None)) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid Authorization format. Use: Bearer <token>")
    return parts[1]

async def get_current_user(authorization: str | None = Header(None)) -> User:
    token = _get_token(authorization)
    user = _auth_manager.get_user_by_token(token)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    return user

async def get_admin_user(authorization: str | None = Header(None)) -> User:
    token = _get_token(authorization)
    user = _auth_manager.get_user_by_token(token)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
