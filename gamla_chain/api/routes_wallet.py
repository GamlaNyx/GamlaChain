from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from gamla_chain.api.middleware import get_current_user
from gamla_chain.core.auth import User

router = APIRouter(prefix="/api/v1/wallet")

_wallet_manager = None
_blockchain = None
_auth = None

def init_wallet_routes(wallet_manager, blockchain, auth_manager=None):
    global _wallet_manager, _blockchain, _auth
    _wallet_manager = wallet_manager
    _blockchain = blockchain
    _auth = auth_manager

class CreateWalletRequest(BaseModel):
    label: str = Field(default="", max_length=64)

class CreateTransactionRequest(BaseModel):
    sender_address: str
    receiver_address: str
    amount: float = Field(..., gt=0)
    private_key: str

@router.post("/create")
async def create_wallet(req: CreateWalletRequest, user: User = Depends(get_current_user)):
    label = req.label.strip() if req.label.strip() else None
    wallet = _wallet_manager.create_wallet(user.id, label)
    return {"ok": True, "wallet": {"address": wallet["address"], "private_key": wallet["private_key"], "label": wallet["label"], "created_at": wallet["created_at"]}}

@router.get("/list")
async def list_wallets(user: User = Depends(get_current_user)):
    wallets = _wallet_manager.get_user_wallets(user.id)
    return {"ok": True, "wallets": [{"address": w["address"], "label": w["label"], "created_at": w["created_at"]} for w in wallets]}

@router.get("/{address}/balance")
async def get_balance(address: str):
    balance = _blockchain.get_balance(address)
    return {"ok": True, "address": address, "balance": balance}

@router.get("/{address}/history")
async def get_history(address: str):
    history = _blockchain.get_transaction_history(address)
    return {"ok": True, "address": address, "transactions": [tx.to_dict() for tx in history], "count": len(history)}

@router.post("/send")
async def send_transaction(req: CreateTransactionRequest, user: User = Depends(get_current_user)):
    sender_wallet = _wallet_manager.get_wallet_by_address(req.sender_address)
    if sender_wallet is None:
        raise HTTPException(status_code=404, detail="Sender wallet not found")
    if sender_wallet["user_id"] != user.id:
        raise HTTPException(status_code=403, detail="Sender wallet does not belong to you")
    if sender_wallet["private_key"] != req.private_key:
        raise HTTPException(status_code=403, detail="Invalid private key")
    balance = _blockchain.get_balance(req.sender_address)
    if balance < req.amount:
        raise HTTPException(status_code=400, detail=f"Insufficient balance. Have: {balance}, Need: {req.amount}")
    from gamla_chain.core.transaction import Transaction
    import time
    tx = Transaction(sender=req.sender_address, receiver=req.receiver_address, amount=req.amount, timestamp=time.time())
    _blockchain.add_transaction(tx)
    return {"ok": True, "message": "Transaction added to pool", "tx_hash": tx.tx_hash}


@router.get("/directory")
async def user_directory(user: User = Depends(get_current_user)):
    """Public user directory — list all users with their main wallet address."""
    if _auth is None:
        return {"ok": True, "users": []}
    users = []
    for u in _auth.users.values():
        wallets = _wallet_manager.get_user_wallets(u.id)
        main_wallet = wallets[0]["address"] if wallets else None
        users.append({
            "username": u.username,
            "role": u.role,
            "main_wallet": main_wallet,
            "wallet_count": len(wallets),
        })
    return {"ok": True, "users": users}
