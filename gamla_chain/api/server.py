from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from gamla_chain.api.routes import router as chain_router
from gamla_chain.api.routes_auth import router as auth_router
from gamla_chain.api.routes_wallet import router as wallet_router
from gamla_chain.api.routes_admin import router as admin_router
from gamla_chain.api.routes_faucet import router as faucet_router


def create_app(static_dir: str = "frontend") -> FastAPI:
    app = FastAPI(title="GamlaChain API", version="0.2.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(chain_router)
    app.include_router(auth_router)
    app.include_router(wallet_router)
    app.include_router(admin_router)
    app.include_router(faucet_router)

    static_path = Path(static_dir)
    if static_path.exists():
        app.mount("/css", StaticFiles(directory=str(static_path / "css")), name="css")
        # Mount frontend at root so /index.html, /login.html, etc. resolve directly.
        # API routes (/api/v1/*) take priority over static files.
        app.mount("/", StaticFiles(directory=str(static_path), html=True), name="static")

    return app
