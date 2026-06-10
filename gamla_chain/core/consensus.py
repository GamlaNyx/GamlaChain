from gamla_chain.core.block import Block


def proof_of_work(block: Block, difficulty: int) -> Block:
    """Simple Proof of Work: find a nonce that makes the hash start with `difficulty` zeros."""
    target = "0" * difficulty
    block.nonce = 0
    block.hash = block.compute_hash()
    while not block.hash.startswith(target):
        block.nonce += 1
        block.hash = block.compute_hash()
    return block


def is_valid_proof(block: Block, difficulty: int) -> bool:
    return block.hash.startswith("0" * difficulty) and block.hash == block.compute_hash()
