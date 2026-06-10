import pytest

from gamla_chain.core.chain import Blockchain
from gamla_chain.core.transaction import Transaction
from gamla_chain.core.wallet import Wallet


class TestBlockchain:
    @pytest.fixture
    def chain(self):
        return Blockchain(difficulty=3, mining_reward=50.0)

    def test_genesis_block(self, chain):
        assert len(chain.chain) == 1
        genesis = chain.chain[0]
        assert genesis.index == 0
        assert genesis.previous_hash == "0"
        assert len(genesis.hash) == 64

    def test_mine_block(self, chain):
        alice = Wallet()
        chain.mine_pending_transactions(alice.address)
        assert len(chain.chain) == 2
        assert chain.is_chain_valid()

    def test_add_transaction(self, chain):
        alice = Wallet()
        bob = Wallet()
        chain.mine_pending_transactions(alice.address)
        tx = Transaction(alice.address, bob.address, 25.0)
        chain.add_transaction(tx)
        assert len(chain.pending_transactions) == 1  # only the new tx

    def test_balance(self, chain):
        alice = Wallet()
        bob = Wallet()
        chain.mine_pending_transactions(alice.address)
        chain.add_transaction(Transaction(alice.address, bob.address, 20.0))
        chain.mine_pending_transactions(bob.address)
        assert chain.get_balance(alice.address) == 30.0  # 50 reward - 20 sent
        assert chain.get_balance(bob.address) == 70.0   # 20 received + 50 reward

    def test_chain_invalid_on_tamper(self, chain):
        alice = Wallet()
        chain.mine_pending_transactions(alice.address)
        chain.chain[1].transactions[0].amount = 999999.0
        assert not chain.is_chain_valid()

    def test_valid_chain_accepts_good_chain(self, chain):
        alice = Wallet()
        chain.mine_pending_transactions(alice.address)
        chain_dict = [b.to_dict() for b in chain.chain]
        assert chain.valid_chain(chain_dict)

    def test_valid_chain_rejects_broken_link(self, chain):
        alice = Wallet()
        chain.mine_pending_transactions(alice.address)
        chain_dict = [b.to_dict() for b in chain.chain]
        chain_dict[1]["previous_hash"] = "0xdeadbeef"
        assert not chain.valid_chain(chain_dict)

    def test_valid_chain_rejects_invalid_proof(self, chain):
        alice = Wallet()
        chain.mine_pending_transactions(alice.address)
        chain_dict = [b.to_dict() for b in chain.chain]
        chain_dict[1]["hash"] = "0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
        assert not chain.valid_chain(chain_dict)

    def test_register_node(self, chain):
        chain.register_node("http://192.168.0.5:5000")
        assert "192.168.0.5:5000" in chain.nodes

    def test_register_node_idempotent(self, chain):
        chain.register_node("http://192.168.0.5:5000")
        chain.register_node("http://192.168.0.5:5000")
        assert len([n for n in chain.nodes if n == "192.168.0.5:5000"]) == 1

    def test_node_identifier_is_set(self, chain):
        assert chain.node_identifier
        assert len(chain.node_identifier) == 32  # uuid4 hex without dashes
