import uvicorn
from gamla_chain.config import Config
from gamla_chain.core.persistence import PersistenceManager
from gamla_chain.core.auth import AuthManager
from gamla_chain.core.wallet_manager import WalletManager
from gamla_chain.core.blockchain_manager import manager
from gamla_chain.core.block import Block
from gamla_chain.api.middleware import init_auth_middleware
from gamla_chain.api.routes_auth import init_auth_routes
from gamla_chain.api.routes_wallet import init_wallet_routes
from gamla_chain.api.routes_admin import init_admin_routes
from gamla_chain.api.routes_faucet import init_faucet_routes
from gamla_chain.api.server import create_app


def main():
    config = Config.from_env()

    persistence = PersistenceManager(data_dir=config.data_dir)
    auth_manager = AuthManager(persistence)
    wallet_manager = WalletManager(persistence)

    chain_data = persistence.load("chain")
    if chain_data:
        saved_chain = chain_data.get("chain", [])
        if saved_chain:
            manager.blockchain.chain = [Block.from_dict(b) for b in saved_chain]
        saved_pending = chain_data.get("pending_transactions", [])
        if saved_pending:
            from gamla_chain.core.transaction import Transaction
            manager.blockchain.pending_transactions = [Transaction.from_dict(tx) for tx in saved_pending]
        print(f"[startup] Restored chain: {len(manager.blockchain.chain)} blocks, {len(manager.blockchain.pending_transactions)} pending txs")

    def chain_persist_callback(data):
        persistence.save("chain", data)

    manager.blockchain.set_persist_callback(chain_persist_callback)

    init_auth_middleware(auth_manager)
    init_auth_routes(auth_manager, wallet_manager)
    init_wallet_routes(wallet_manager, manager.blockchain)
    init_admin_routes(auth_manager, wallet_manager, manager.blockchain)
    init_faucet_routes(wallet_manager, manager.blockchain, persistence)

    app = create_app(config)
    print(f"[startup] GamlaChain v0.2.0 starting on {config.host}:{config.port}")
    print(f"[startup] Data dir: {config.data_dir}")
    print(f"[startup] Users registered: {len(auth_manager.users)}")

    uvicorn.run(app, host=config.host, port=config.port)


if __name__ == "__main__":
    main()
