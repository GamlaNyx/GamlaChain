# GamlaChain

基于 Python 的区块链教学项目。遵循 [Learn Blockchains by Building One](https://hackernoon.com/learn-blockchains-by-building-one) 教程构建，并扩展了多节点共识、REST API、玻璃拟态前端浏览器等完整功能。

## 功能特性

- **区块链核心** — Block、Transaction、Wallet，SHA-256 哈希
- **工作量证明 (PoW)** — 可配置难度、矿工奖励
- **共识算法** — 最长链规则 + 多节点网状网络 + 自动同步
- **REST API** — 11 个 FastAPI 端点（`/docs` 提供 Swagger 文档）
- **前端浏览器** — 玻璃拟态 SPA，支持单节点/多节点模式、Chart.js 图表、中文界面
- **区块可视化** — 区块链卡片式展示，点击查看详情
- **地址浏览器** — 查询余额和交易历史
- **模拟交易** — 一键自动交易 + 出块，多节点模式下模拟真实区块链行为（TX 广播 → 单节点挖矿 → 自动共识同步）

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 命令行演示
python scripts/demo.py

# 启动 API 服务器
python -m gamla_chain
# → http://127.0.0.1:8000
# → Swagger: http://127.0.0.1:8000/docs

# 打开前端浏览器
# 浏览器打开 frontend/index.html
```

## 多节点共识

多节点模式下模拟真实区块链行为：

```
TX 广播到所有节点 → 节点 0 挖矿出块 → 其余节点自动共识同步
                        ↓
              全网维护同一条链的副本
```

### 手动操作

```bash
# 终端 1 — 节点 A (矿工)
python -m gamla_chain

# 终端 2 — 节点 B (同步节点)
python -m uvicorn gamla_chain.api.server:app --port 8001

# 终端 3 — 节点 C (可选)
python -m uvicorn gamla_chain.api.server:app --port 8002

# 注册节点 A ↔ B
curl -X POST http://127.0.0.1:8000/api/v1/nodes/register \
  -H "Content-Type: application/json" \
  -d '{"nodes": ["http://127.0.0.1:8001"]}'

curl -X POST http://127.0.0.1:8001/api/v1/nodes/register \
  -H "Content-Type: application/json" \
  -d '{"nodes": ["http://127.0.0.1:8000"]}'

# 在节点 A 挖矿
curl -X POST "http://127.0.0.1:8000/api/v1/mine?miner_address=miner"

# 节点 B 同步
curl http://127.0.0.1:8001/api/v1/nodes/resolve
```

### 前端一键操作

切换到 **多节点** 模式 → 添加节点 URL → 点击 **模拟交易**：
- 自动 Mesh 注册所有节点
- TX 同时广播到所有节点
- 节点 0 挖矿后自动触发共识同步
- 状态栏实时显示同步计数

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/chain` | 完整区块链数据 |
| GET | `/api/v1/blocks/latest` | 最新区块 |
| GET | `/api/v1/blocks/{index}` | 按高度查区块 |
| POST | `/api/v1/transactions` | 创建交易 |
| GET | `/api/v1/transactions/pending` | 待打包交易池 |
| POST | `/api/v1/mine` | 挖矿出块 |
| GET | `/api/v1/balance/{address}` | 地址余额 |
| GET | `/api/v1/history/{address}` | 地址交易历史 |
| GET | `/api/v1/validate` | 校验本地区块链 |
| POST | `/api/v1/nodes/register` | 注册邻居节点 |
| GET | `/api/v1/nodes/resolve` | 触发共识决议 |

## 项目结构

```
GamlaChain/
├── gamla_chain/              # 主包
│   ├── core/                 #   区块链核心 (block, chain, consensus, wallet)
│   ├── api/                  #   FastAPI REST 层 (server, routes)
│   ├── utils/                #   工具函数 (crypto, serializer)
│   ├── config.py             #   全局配置
│   └── __main__.py           #   启动入口
├── frontend/
│   └── index.html            #   区块链浏览器 SPA (1052 行, 中文界面)
├── scripts/
│   └── demo.py               #   CLI 演示脚本
├── tests/
│   └── test_chain.py         #   11 项单元测试
├── docs/
│   ├── design.md             #   设计文档
│   └── usage.md              #   使用文档
├── README.md                 #   项目说明
├── LICENSE                   #   MIT
└── requirements.txt
```

## 配置

环境变量或 `.env` 文件：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `HOST` | `127.0.0.1` | API 监听地址 |
| `PORT` | `8000` | API 监听端口 |
| `MINING_DIFFICULTY` | `4` | PoW 难度 (前导零个数) |
| `MINING_REWARD` | `50.0` | 出块奖励 (GLC) |

## 测试

```bash
python -m pytest tests/ -v
# 11 项测试: chain, consensus, validation, node registration
```

## License

MIT — 详见 [LICENSE](LICENSE)
