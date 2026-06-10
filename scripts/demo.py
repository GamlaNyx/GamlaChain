"""Demo script: run a local blockchain simulation and print the results."""
import sys
sys.path.insert(0, ".")

from gamla_chain.core.chain import Blockchain
from gamla_chain.core.transaction import Transaction
from gamla_chain.core.wallet import Wallet
from gamla_chain.utils.serializer import to_json


def main():
    print("=" * 50)
    print("GamlaChain - Blockchain Demo")
    print("=" * 50)

    chain = Blockchain(difficulty=4, mining_reward=50.0)

    alice = Wallet()
    bob = Wallet()
    charlie = Wallet()

    print(f"\n[Wallets]")
    print(f"  Alice  : {alice.address[:16]}...")
    print(f"  Bob    : {bob.address[:16]}...")
    print(f"  Charlie: {charlie.address[:16]}...")

    print("\n[Mining genesis reward -> Alice]")
    chain.mine_pending_transactions(alice.address)
    print(f"  Alice balance: {chain.get_balance(alice.address)}")

    print("\n[Transactions]")
    chain.add_transaction(Transaction(alice.address, bob.address, 20.0))
    chain.add_transaction(Transaction(alice.address, charlie.address, 10.0))
    chain.add_transaction(Transaction(bob.address, charlie.address, 5.0))
    print("  Added: Alice -> Bob (20), Alice -> Charlie (10), Bob -> Charlie (5)")

    print("\n[Mining block #2 -> Bob]")
    chain.mine_pending_transactions(bob.address)
    print(f"  Bob balance: {chain.get_balance(bob.address)}")

    print("\n[Balances]")
    print(f"  Alice  : {chain.get_balance(alice.address)}")
    print(f"  Bob    : {chain.get_balance(bob.address)}")
    print(f"  Charlie: {chain.get_balance(charlie.address)}")

    print(f"\n[Chain Valid?] {chain.is_chain_valid()}")
    print(f"[Block count] {len(chain.chain)}")

    for block in chain.chain:
        print(f"\n  Block #{block.index}")
        print(f"    Hash: {block.hash[:32]}...")
        print(f"    Prev: {block.previous_hash[:32]}...")
        print(f"    Nonce: {block.nonce}")
        print(f"    TXs : {len(block.transactions)}")

    print("\n" + "=" * 50)
    print("Demo complete. Run the API server with: python -m gamla_chain")
    print("=" * 50)


if __name__ == "__main__":
    main()
