import uvicorn

from gamla_chain.config import default_config


def main():
    uvicorn.run(
        "gamla_chain.api.server:app",
        host=default_config.host,
        port=default_config.port,
        reload=True,
    )


if __name__ == "__main__":
    main()
