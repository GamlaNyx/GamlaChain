# GamlaChain

A simple blockchain implementation in Python for educational purposes. Built following the [Learn Blockchains by Building One](https://hackernoon.com/learn-blockchains-by-building-one) tutorial, with extended features including multi-node consensus, REST API, and a glassmorphism frontend explorer.

## Features

- **Blockchain Core** — Block, Transaction, Wallet with SHA-256 hashing
- **Proof of Work** — Configurable difficulty, coinbase rewards
- **Consensus** — Longest-chain rule with multi-node mesh network
- **REST API** — 11 FastAPI endpoints (Swagger docs at `/docs`)
- **Frontend Explorer** — Glassmorphism SPA with single / multi-node modes, Chart.js visualizations
- **Multi-node Support** — Register nodes, resolve conflicts, compare chains side-by-side

## Quick Start

```bash
# Install
pip install -r requirements.txt

# Run demo
python scripts/demo.py

# Start API server
python -m gamla_chain
# → http://127.0.0.1:8000
# → Swagger: http://127.0.0.1:8000/docs

# Open frontend explorer
# Open frontend/index.html in your browser
```

## Multi-Node Consensus

```bash
# Terminal 1 — Node A
python -m gamla_chain

# Terminal 2 — Node B
python -m uvicorn gamla_chain.api.server:app --port 8001

# Register nodes (via API or frontend)
curl -X POST http://127.0.0.1:8000/api/v1/nodes/register \
  -H "Content-Type: application/json" \
  -d '{"nodes": ["http://127.0.0.1:8001"]}'

curl -X POST http://127.0.0.1:8001/api/v1/nodes/register \
  -H "Content-Type: application/json" \
  -d '{"nodes": ["http://127.0.0.1:8000"]}'

# Mine on Node B to create a longer chain, then resolve on Node A
curl http://127.0.0.1:8000/api/v1/nodes/resolve
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/chain` | Full blockchain data |
| GET | `/api/v1/blocks/latest` | Latest block |
| GET | `/api/v1/blocks/{index}` | Block by height |
| POST | `/api/v1/transactions` | Create transaction |
| GET | `/api/v1/transactions/pending` | Pending transaction pool |
| POST | `/api/v1/mine` | Mine a new block |
| GET | `/api/v1/balance/{address}` | Address balance |
| GET | `/api/v1/history/{address}` | Transaction history |
| GET | `/api/v1/validate` | Validate local chain |
| POST | `/api/v1/nodes/register` | Register neighbour nodes |
| GET | `/api/v1/nodes/resolve` | Trigger consensus resolution |

## Project Structure

```
GamlaChain/
├── gamla_chain/              # Main package
│   ├── core/                 #   Blockchain logic
│   ├── api/                  #   FastAPI REST layer
│   ├── utils/                #   Hashing, serialization
│   ├── config.py             #   Configuration
│   └── __main__.py           #   Entry point
├── frontend/
│   └── index.html            #   Blockchain explorer SPA
├── scripts/
│   └── demo.py               #   CLI demo
├── tests/
│   └── test_chain.py         #   11 unit tests
├── docs/
│   ├── design.md             #   Design document
│   └── usage.md              #   Usage guide
├── LICENSE                   #   MIT
└── requirements.txt
```

## Configuration

Via environment variables or `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `127.0.0.1` | API bind address |
| `PORT` | `8000` | API port |
| `MINING_DIFFICULTY` | `4` | PoW leading zeros |
| `MINING_REWARD` | `50.0` | Block reward in GLC |

## Testing

```bash
python -m pytest tests/ -v
# 11 tests: chain, consensus, validation, node registration
```

## License

MIT — see [LICENSE](LICENSE) for details.
