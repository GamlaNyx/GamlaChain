from dataclasses import asdict

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from gamla_chain.core.blockchain_manager import manager
from gamla_chain.core.transaction import Transaction

router = APIRouter(prefix="/api/v1")


class RegisterNodesRequest(BaseModel):
    nodes: list[str]


@router.get("/chain")
async def get_chain():
    chain_data = manager.blockchain.to_dict()
    return {"ok": True, "data": chain_data}


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


@router.get("/blocks/latest")
async def get_latest_block():
    block = manager.blockchain.last_block
    return {"ok": True, "data": block.to_dict()}


@router.get("/blocks/{index}")
async def get_block(index: int):
    chain = manager.blockchain.chain
    if index < 0 or index >= len(chain):
        raise HTTPException(status_code=404, detail="Block not found")
    return {"ok": True, "data": chain[index].to_dict()}


@router.get("/transactions/pending")
async def get_pending_transactions():
    txs = [tx.to_dict() for tx in manager.blockchain.pending_transactions]
    return {"ok": True, "data": txs, "count": len(txs)}


@router.post("/transactions")
async def create_transaction(tx: Transaction):
    # Block fake system senders (reserved for mining/faucet)
    if tx.sender in ("network", "faucet"):
        raise HTTPException(status_code=403, detail="Reserved sender address")
    index = manager.blockchain.add_transaction(tx)
    return {"ok": True, "message": "Transaction added to pool", "pool_index": index}


@router.post("/mine")
async def mine_block(miner_address: str = Query(default="miner1")):
    """Public mining — anyone can mine pending transactions into a block."""
    block = manager.blockchain.mine_pending_transactions(miner_address)
    return {"ok": True, "message": "Block mined", "data": block.to_dict()}


@router.get("/balance/{address}")
async def get_balance(address: str):
    balance = manager.blockchain.get_balance(address)
    return {"ok": True, "address": address, "balance": balance}


@router.get("/history/{address}")
async def get_history(address: str):
    history = manager.blockchain.get_transaction_history(address)
    return {
        "ok": True,
        "address": address,
        "transactions": [tx.to_dict() for tx in history],
        "count": len(history),
    }


@router.get("/validate")
async def validate_chain():
    valid = manager.blockchain.is_chain_valid()
    return {"ok": True, "valid": valid}


@router.post("/nodes/register")
async def register_nodes(req: RegisterNodesRequest):
    if not req.nodes:
        raise HTTPException(status_code=400, detail="Please supply a valid list of nodes")
    for node in req.nodes:
        manager.blockchain.register_node(node)
    return {
        "ok": True,
        "message": "New nodes have been added",
        "total_nodes": list(manager.blockchain.nodes),
    }


@router.get("/nodes/resolve")
async def consensus():
    replaced = manager.blockchain.resolve_conflicts()
    if replaced:
        return {
            "ok": True,
            "message": "Our chain was replaced",
            "new_chain": [b.to_dict() for b in manager.blockchain.chain],
        }
    return {
        "ok": True,
        "message": "Our chain is authoritative",
        "chain": [b.to_dict() for b in manager.blockchain.chain],
    }
