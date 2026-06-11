# GamlaChain 开发者指南

## 1. 项目总览

```
GamlaChain/
├── gamla_chain/                    # Python 后端包
│   ├── core/                       #   区块链核心逻辑
│   │   ├── block.py                #     区块数据结构
│   │   ├── transaction.py          #     交易数据结构
│   │   ├── chain.py                #     区块链主类 + 共识
│   │   ├── consensus.py            #     工作量证明 (PoW)
│   │   ├── wallet.py               #     简易钱包
│   │   └── blockchain_manager.py   #     全局区块链单例
│   ├── api/                        #   REST API 层
│   │   ├── server.py               #     FastAPI 应用
│   │   └── routes.py               #     11 个 API 端点
│   ├── utils/                      #   工具模块
│   │   ├── crypto.py               #     SHA-256 哈希
│   │   └── serializer.py           #     JSON 序列化
│   ├── config.py                   #   配置管理
│   └── __main__.py                 #   启动入口
├── frontend/
│   └── index.html                  # 前端 SPA (~1085 行)
├── scripts/demo.py                 # 命令行演示
├── tests/test_chain.py             # 11 项单元测试
├── docs/                           # 文档
├── requirements.txt                # Python 依赖
└── pyproject.toml                  # 项目元数据
```

---

## 2. 数据流架构

```
HTTP Request (前端/curl)
    │
    ▼
┌─────────────────────────────────────────────┐
│ api/routes.py — FastAPI 路由层               │
│ 参数校验 → 调用 Blockchain 方法 → 返回 JSON  │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│ core/chain.py — Blockchain 核心逻辑          │
│ 管理链数据、交易池、节点注册、共识决议        │
└───┬─────────────┬───────────────┬───────────┘
    │             │               │
    ▼             ▼               ▼
┌────────┐ ┌────────────┐ ┌──────────────┐
│ block  │ │ transaction│ │ consensus    │
│ .py    │ │ .py        │ │ .py          │
│ Block  │ │ Transaction│ │ proof_of_work│
│ 数据结构│ │ 数据结构   │ │ is_valid_proof│
└────────┘ └────────────┘ └──────────────┘
    │             │
    ▼             ▼
┌────────────────────────────┐
│ utils/crypto.py            │
│ sha256() hash_block()      │
│ hash_transaction()         │
└────────────────────────────┘
```

---

## 3. 核心模块详解

### 3.1 `core/block.py` — 区块

```python
@dataclass
class Block:
    index: int             # 区块高度 (0 = 创世块)
    previous_hash: str     # 前块哈希 (创世块为 "0")
    timestamp: float       # Unix 时间戳 (自动生成)
    transactions: list     # Transaction 列表
    nonce: int             # PoW 随机数 (0 起始)
    hash: str              # 区块哈希 (SHA-256)
```

| 方法 | 功能 | 实现逻辑 |
|------|------|---------|
| `compute_hash()` | 计算区块哈希 | 将 index + previous_hash + timestamp + transactions(转dict) + nonce 序列化为 JSON → SHA-256 |
| `to_dict()` | 序列化为字典 | 递归调用 Transaction.to_dict()，返回纯 dict 用于 JSON 响应 |
| `from_dict(data)` | 从字典反序列化 | 类方法，递归还原 Transaction 对象，用于共识同步时重建外部链 |

### 3.2 `core/transaction.py` — 交易

```python
@dataclass
class Transaction:
    sender: str            # 发送方地址
    receiver: str          # 接收方地址
    amount: float          # 金额
    timestamp: float       # Unix 时间戳 (自动生成)
    tx_hash: str           # 交易哈希 (自动生成)
```

| 方法 | 功能 | 实现逻辑 |
|------|------|---------|
| `__post_init__()` | 自动生成哈希 | 如果 tx_hash 为空，调用 compute_hash() |
| `compute_hash()` | 计算交易哈希 | SHA-256(sender + receiver + amount + timestamp) |
| `to_dict()` | 序列化 | 返回纯 dict |
| `from_dict(data)` | 反序列化 | 类方法，从字典重建 Transaction |

### 3.3 `core/chain.py` — 区块链主类

这是整个项目的核心，管理链数据、交易池、节点网络和共识。

```python
@dataclass
class Blockchain:
    chain: list[Block]                    # 完整区块链
    pending_transactions: list[Transaction]  # 待打包交易池
    difficulty: int = 4                   # PoW 难度 (前导零个数)
    mining_reward: float = 50.0           # 出块奖励 (GLC)
    nodes: set[str]                       # 邻居节点集合 (幂等)
    node_identifier: str                  # 本节点 UUID
```

| 方法 | 功能 | 实现逻辑 |
|------|------|---------|
| `__post_init__()` | 初始化链 | 如果链为空，自动创建并挖出创世块 |
| `_create_genesis_block()` | 创建创世块 | index=0, previous_hash="0", 执行 PoW |
| `last_block` (property) | 获取最新区块 | 返回 `chain[-1]` |
| `add_transaction(tx)` | 添加交易到待打包池 | append → 返回池中索引 |
| `mine_pending_transactions(miner)` | 挖矿打包 | ① 创建 coinbase 奖励交易 ② 与待打包交易合并 ③ 执行 PoW ④ 追加到链 ⑤ 清空待打包池 |
| `is_chain_valid()` | 校验本地区块链 | 逐块验证 previous_hash 链接 + PoW 有效性 |
| `get_balance(address)` | 查询余额 | 遍历链上所有交易，收+支- |
| `get_transaction_history(address)` | 查询交易历史 | 遍历所有区块，筛选涉及该地址的交易 |
| `register_node(address)` | 注册邻居节点 | 解析 URL 提取 netloc，加入 nodes 集合 (set 自动去重) |
| `valid_chain(external_chain)` | 验证外部链 | 逐块验证: ① hash 链接 ② hash 计算正确 ③ 满足难度要求 |
| `resolve_conflicts()` | 共识决议 | HTTP GET 所有邻居的 /chain → valid_chain 验证 → 用最长有效链替换本地链 |
| `to_dict()` | 序列化 | 返回完整链数据 + 元信息 |

**多节点工作流 (resolve_conflicts):**
```
1. for each neighbour in self.nodes:
2.     GET http://{neighbour}/api/v1/chain
3.     解析 JSON → 获取 chain + length
4.     if length > 本地链长度 and valid_chain(外部链):
5.         记录为候选
6. if 存在候选: 替换 self.chain → return True
7. else: return False (本地区块链为权威)
```

### 3.4 `core/consensus.py` — 工作量证明

| 函数 | 功能 | 实现逻辑 |
|------|------|---------|
| `proof_of_work(block, difficulty)` | 执行 PoW 挖矿 | target = "0"×difficulty → nonce 从 0 递增 → 每次重算 hash → 直到 hash 以 target 开头 |
| `is_valid_proof(block, difficulty)` | 验证 PoW | hash 以 "0"×difficulty 开头 **且** hash == 重新计算的哈希 |

**算法复杂度：** O(16^difficulty) 期望值。difficulty=4 时约 65,536 次尝试，实测 ~2 秒。

### 3.5 `core/wallet.py` — 钱包

| 方法 | 功能 | 实现逻辑 |
|------|------|---------|
| `__init__` | 生成钱包 | 随机 32 字节 hex 作为私钥 → SHA-256(私钥) 作为地址 |
| `sign(message)` | 签名 | SHA-256(私钥 + 消息)，简化版签名 |
| `from_key(private_key)` | 从私钥恢复 | 类方法，用于导入已有钱包 |

### 3.6 `core/blockchain_manager.py` — 全局单例

```python
manager = type("Manager", (), {"blockchain": Blockchain()})()
```

创建一个匿名类的实例，全局唯一。所有 API 端点共享同一个区块链实例。单进程内的多个请求操作同一条链。

---

## 4. API 层

### 4.1 `api/server.py`

```python
app = FastAPI(title="GamlaChain API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], ...)
app.include_router(router)
```

创建 FastAPI 应用，启用 CORS（允许前端跨域访问），注册路由。

### 4.2 `api/routes.py` — 11 个端点

| 端点 | 方法 | 调用 | 说明 |
|------|------|------|------|
| `/api/v1/chain` | GET | `blockchain.to_dict()` | 完整链数据 + 元信息 |
| `/api/v1/blocks/latest` | GET | `blockchain.last_block` | 最新区块 |
| `/api/v1/blocks/{index}` | GET | `chain[index]` | 按高度查区块，越界返回 404 |
| `/api/v1/transactions/pending` | GET | `pending_transactions` | 待打包池 |
| `/api/v1/transactions` | POST | `add_transaction(tx)` | 创建交易，FastAPI 自动反序列化 JSON → Transaction |
| `/api/v1/mine` | POST | `mine_pending_transactions(miner)` | 挖矿，miner_address 为奖励接收方 |
| `/api/v1/balance/{address}` | GET | `get_balance(address)` | 地址余额 |
| `/api/v1/history/{address}` | GET | `get_transaction_history(address)` | 交易历史(按时间) |
| `/api/v1/validate` | GET | `is_chain_valid()` | 链有效性 |
| `/api/v1/nodes/register` | POST | `register_node(address)` | 注册邻居节点 |
| `/api/v1/nodes/resolve` | GET | `resolve_conflicts()` | 共识决议 |

所有响应统一格式：`{"ok": true, "data": ..., "message": "..."}`

---

## 5. 工具模块

### 5.1 `utils/crypto.py`

| 函数 | 实现 |
|------|------|
| `sha256(data)` | `hashlib.sha256(data.encode()).hexdigest()` |
| `hash_block(index, prev, ts, txs, nonce)` | 将字段序列化为有序 JSON → sha256 |
| `hash_transaction(sender, receiver, amount, ts)` | 将字段序列化为有序 JSON → sha256 |

`sort_keys=True` 保证相同数据产生相同哈希。

### 5.2 `utils/serializer.py`

`ChainEncoder` 继承 `json.JSONEncoder`，自动将 dataclass 对象转为 dict。`to_json()` 便捷方法。

### 5.3 `config.py`

`Config` dataclass 包含 4 个可配置字段。`Config.from_env()` 从环境变量读取（无 .env 文件时使用默认值）。模块级 `default_config` 单例供全局使用。

---

## 6. 前端架构 (`frontend/index.html`)

### 6.1 总体结构

```
┌─ CSS (style) ──────────────────────────────────┐
│ CSS 变量 (颜色/阴影/模糊) + 玻璃拟态组件样式     │
│ 动画: fadeInUp / pulse-glow / orbFloat / newBlockGlow │
└────────────────────────────────────────────────┘
┌─ HTML (body) ──────────────────────────────────┐
│ #viewSingle — 单节点模式                        │
│ #viewMulti  — 多节点模式 (默认隐藏)              │
│ #modalOverlay — 区块/交易详情弹窗                │
│ #toastContainer — 提示消息                      │
└────────────────────────────────────────────────┘
┌─ JavaScript (script) ──────────────────────────┐
│ API 层 → 数据获取 → UI 更新 → 图表渲染 → 模拟   │
└────────────────────────────────────────────────┘
```

### 6.2 JavaScript 模块划分

#### 配置与状态
| 变量 | 用途 |
|------|------|
| `nodeUrls[]` | 节点 URL 列表 (persistent via localStorage) |
| `nodesData[]` | 每个节点的链数据缓存 |
| `mode` | 'single' / 'multi' |
| `lastHeight` / `lastBlockIdx` | 高度增量追踪 / 新区块辉光 |

#### API 层
| 函数 | 功能 |
|------|------|
| `fetchWithTimeout(url, opts)` | 带 AbortController 超时的 fetch (5s) |
| `apiGet(base, path)` | GET 请求，自动解析 JSON |
| `apiPost(base, path, body)` | POST 请求，发送 JSON |
| `fetchNodeData(base)` | 并行请求 chain + pending + validate |

#### 轮询
| 函数 | 实现 |
|------|------|
| `poll()` | 3 秒间隔，单节点调 `fetchNodeData(nodeUrls[0])`，多节点用 `Promise.allSettled` 并行获取所有节点 |

#### UI 渲染
| 函数 | 功能 |
|------|------|
| `updateSingleView()` | 更新统计卡片 + 区块列表 + 待打包 + 链上统计 + 调用图表渲染 |
| `renderBlockList(elId, d)` | 渲染区块列表 (保持滚动位置) |
| `renderPendingList(elId, d, badgeId)` | 渲染待打包交易列表 |
| `renderBlockChainViz(elId, d)` | 渲染区块链可视化 (7 个卡片) |
| `updateSingleCharts(d)` | 渲染 5 个单节点图表 (Chart.js) |
| `updateMultiView()` | 更新多节点统计表 + 区块可视化 + 节点卡片 + 调用 `renderMultiCharts()` |

#### 图表 (Chart.js)
| 函数 | 类型 | 数据 |
|------|------|------|
| `sChart()` | 通用折线/柱状图 | 用于单节点 3 个时序图表 |
| `sDoughnut()` | 环形图 | TX 池饼图 + 链有效性 |
| `mChart()` | 通用折线图 | 用于多节点每节点 2 个图表 |
| `renderMultiCharts()` | 多节点图表演染入口 | 遍历每节点调用 mChart |

#### 搜索与地址
| 函数 | 功能 |
|------|------|
| `doSearch()` | 搜索栏：识别 #数字 (区块查询) 或 0x 地址 (地址查询) |
| `lookupAddress()` | 调用 balance + history API，渲染结果 |
| `navigateBlock(index)` | 区块详情弹窗的 ← → 导航 |

#### 操作
| 函数 | 功能 |
|------|------|
| `mineOnNode(idx)` | 对指定节点 POST /mine |
| `sendTx(idx)` | 对指定节点 POST /transactions |
| `registerAllNodes()` | 对所有节点执行网状注册 |
| `resolveOnSelected()` | 对选中节点执行共识决议 |

#### 模拟交易引擎
| 函数 | 模式 | 行为 |
|------|------|------|
| `toggleSimulation()` | 启动/停止 | 多节点模式自动 Mesh 注册后启动 |
| `scheduleTxSingle(idx)` | 单节点 | 0.05-0.3s 随机间隔，向单节点发 TX |
| `scheduleBlockSingle(idx)` | 单节点 | 2.5s 固定间隔，单节点挖矿 |
| `scheduleTxMulti()` | 多节点 | 0.05-0.3s，同一笔 TX 广播到所有节点 |
| `scheduleBlockMulti()` | 多节点 | 2.5s，节点 0 挖矿 → 其余节点自动 /nodes/resolve |

#### 弹窗
| 函数 | 功能 |
|------|------|
| `showBlockDetail(block)` | 区块详情 (含 ← → 导航、确认数、交易列表) |
| `showTxDetail(tx)` | 交易详情 |

---

## 7. 命令行演示 (`scripts/demo.py`)

创建 3 个钱包 (Alice/Bob/Charlie) → 挖创世块奖励 Alice → 3 笔转账 → 挖块打包 → 打印余额和链信息。

使用了 `core/chain.py` `core/wallet.py` `core/transaction.py`，不依赖 API 层。

---

## 8. 测试 (`tests/test_chain.py`)

11 项测试覆盖：

| 测试 | 验证点 |
|------|--------|
| `test_genesis_block` | 创世块 index=0, previous_hash="0", hash 长度 64 |
| `test_mine_block` | 挖矿后链长度+1, 链有效 |
| `test_add_transaction` | 交易加入待打包池 |
| `test_balance` | Alice 50-20=30, Bob 20+50=70 |
| `test_chain_invalid_on_tamper` | 篡改交易金额后 is_chain_valid()=False |
| `test_valid_chain_accepts_good_chain` | `valid_chain` 接受有效外部链 |
| `test_valid_chain_rejects_broken_link` | 篡改 previous_hash 后拒绝 |
| `test_valid_chain_rejects_invalid_proof` | 篡改 hash 后拒绝 |
| `test_register_node` | 节点注册加入 nodes 集合 |
| `test_register_node_idempotent` | 重复注册同一节点, set 保持唯一 |
| `test_node_identifier_is_set` | node_identifier 为 32 位 hex |

---

## 9. 关键设计决策

| 决策 | 原因 |
|------|------|
| dataclass 而非手写类 | 类型安全, 自动 __init__, 易于序列化 |
| FastAPI 而非 Flask | 异步支持, 自动 OpenAPI 文档, Pydantic 校验 |
| `set()` 存 nodes | 自动去重, O(1) 查找 |
| coinbase 交易在块内 | 挖矿奖励即时到账, 无需等下一个块 |
| `allSettled` 多节点轮询 | 一个节点离线不影响其他节点渲染 |
| `normalizeUrl()` 去尾斜杠 | 防止 `baseUrl/ + /path` → `//path` 导致 404 |
| `AbortController` 5s 超时 | 防止无响应节点阻塞整个 UI |
| 前端单文件 | 零构建步骤, 浏览器直接打开即可使用 |
