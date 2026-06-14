"""Faucet endpoint — users can claim test tokens a limited number of times."""
import time
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from gamla_chain.api.middleware import get_current_user
from gamla_chain.core.auth import User

router = APIRouter(prefix="/api/v1/faucet")

_wallet_manager = None
_blockchain = None
_persistence = None

# In-memory claim tracker: {user_id: count}
_claims: dict[str, int] = {}

MAX_CLAIMS = 3
CLAIM_AMOUNT = 10.0


def init_faucet_routes(wallet_manager, blockchain, persistence):
    global _wallet_manager, _blockchain, _persistence, _claims
    _wallet_manager = wallet_manager
    _blockchain = blockchain
    _persistence = persistence
    # Restore claims from disk
    saved = _persistence.load("faucet")
    if saved:
        _claims = saved


def _save_claims():
    if _persistence:
        _persistence.save("faucet", _claims)


class ClaimRequest(BaseModel):
    wallet_address: str


@router.get("/info")
async def faucet_info(user: User = Depends(get_current_user)):
    """Get faucet status for the current user."""
    count = _claims.get(user.id, 0)
    remaining = max(0, MAX_CLAIMS - count)
    return {
        "ok": True,
        "data": {
            "claimed": count,
            "remaining": remaining,
            "max_claims": MAX_CLAIMS,
            "claim_amount": CLAIM_AMOUNT,
        },
    }


@router.post("/claim")
async def claim_faucet(req: ClaimRequest, user: User = Depends(get_current_user)):
    """Claim test tokens. Returns the transaction on success."""
    # Check claim limit
    count = _claims.get(user.id, 0)
    if count >= MAX_CLAIMS:
        raise HTTPException(
            status_code=429,
            detail=f"Claim limit reached. You have claimed {count}/{MAX_CLAIMS} times.",
        )

    # Verify wallet belongs to user
    wallet = _wallet_manager.get_wallet_by_address(req.wallet_address)
    if wallet is None:
        raise HTTPException(status_code=404, detail="Wallet not found")
    if wallet["user_id"] != user.id:
        raise HTTPException(status_code=403, detail="Wallet does not belong to you")

    # Create faucet transaction
    from gamla_chain.core.transaction import Transaction
    tx = Transaction(
        sender="faucet",
        receiver=req.wallet_address,
        amount=CLAIM_AMOUNT,
        timestamp=time.time(),
    )
    _blockchain.add_transaction(tx)

    # Update claim count
    _claims[user.id] = count + 1
    _save_claims()

    return {
        "ok": True,
        "message": f"Claimed {CLAIM_AMOUNT} GLC! ({_claims[user.id]}/{MAX_CLAIMS} used)",
        "tx_hash": tx.tx_hash,
        "remaining": MAX_CLAIMS - _claims[user.id],
    }
