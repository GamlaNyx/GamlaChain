from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from gamla_chain.api.routes import router as chain_router
from gamla_chain.api.routes_auth import router as auth_router
from gamla_chain.api.routes_wallet import router as wallet_router
from gamla_chain.api.routes_admin import router as admin_router
from gamla_chain.api.routes_faucet import router as faucet_router
from gamla_chain.config import Config


def create_app(config: Config | None = None) -> FastAPI:
    if config is None:
        config = Config()
    app = FastAPI(
        title="GamlaChain API",
        version="0.2.0",
        docs_url=None if config.cors_origins != "*" else "/docs",  # Hide docs in production
        redoc_url=None,
    )

    # CORS: use configured origins, "*" by default for development
    origins = [o.strip() for o in config.cors_origins.split(",")] if config.cors_origins != "*" else ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "Authorization"],
    )

    app.include_router(chain_router)
    app.include_router(auth_router)
    app.include_router(wallet_router)
    app.include_router(admin_router)
    app.include_router(faucet_router)

    static_path = Path(config.static_dir)
    if static_path.exists():
        app.mount("/css", StaticFiles(directory=str(static_path / "css")), name="css")
        # Mount frontend at root so /index.html, /login.html, etc. resolve directly.
        # API routes (/api/v1/*) take priority over static files.
        app.mount("/", StaticFiles(directory=str(static_path), html=True), name="static")

    return app
