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
    total_supply = sum(tx.amount for b in chain.chain for tx in b.transactions if tx.sender == "network")
    return {"ok": True, "data": {"height": len(chain.chain), "difficulty": chain.difficulty, "mining_reward": chain.mining_reward, "total_transactions": total_tx, "total_supply": total_supply, "pending_count": len(chain.pending_transactions), "nodes": list(chain.nodes), "node_id": chain.node_identifier, "user_count": len(_admin_auth.users), "wallet_count": len(_admin_wm.wallets)}}

@router.get("/chain")
async def get_full_chain(user: User = Depends(get_admin_user)):
    return {"ok": True, "data": _admin_chain.to_dict()}

@router.get("/pending")
async def get_pending(user: User = Depends(get_admin_user)):
    txs = [tx.to_dict() for tx in _admin_chain.pending_transactions]
    return {"ok": True, "data": txs, "count": len(txs)}

@router.post("/mine")
async def mine_block(miner_address: str = Query(default="admin_miner"), user: User = Depends(get_admin_user)):
    block = _admin_chain.mine_pending_transactions(miner_address)
    return {"ok": True, "message": "Block mined", "data": block.to_dict()}

@router.get("/users")
async def list_users(user: User = Depends(get_admin_user)):
    users = []
    for u in _admin_auth.users.values():
        wallets = _admin_wm.get_user_wallets(u.id)
        users.append({"id": u.id, "username": u.username, "role": u.role, "created_at": u.created_at, "wallet_count": len(wallets)})
    return {"ok": True, "users": users}
