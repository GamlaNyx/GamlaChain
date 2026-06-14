from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from gamla_chain.api.middleware import get_current_user
from gamla_chain.core.auth import User

router = APIRouter(prefix="/api/v1/auth")

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
    _wallet_manager.create_wallet(user.id, "主钱包")
    return {"ok": True, "message": "Registration successful", "role": user.role}

@router.post("/login")
async def login(req: LoginRequest):
    session = _auth_manager.login(req.username, req.password)
    if session is None:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    user = _auth_manager.get_user_by_token(session.token)
    return {"ok": True, "token": session.token, "role": user.role, "username": user.username}

@router.post("/logout")
async def logout(user: User = Depends(get_current_user)):
    return {"ok": True, "message": "Logged out"}

@router.get("/me")
async def me(user: User = Depends(get_current_user)):
    wallets = _wallet_manager.get_user_wallets(user.id)
    return {
        "ok": True,
        "user": {"id": user.id, "username": user.username, "role": user.role, "created_at": user.created_at},
        "wallets": [{"address": w["address"], "label": w["label"], "created_at": w["created_at"]} for w in wallets],
    }
