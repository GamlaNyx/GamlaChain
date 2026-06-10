"""Singleton manager for the blockchain instance."""
from gamla_chain.core.chain import Blockchain

manager = type("Manager", (), {"blockchain": Blockchain()})()
