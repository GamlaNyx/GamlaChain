# GamlaChain 设计文档

## 1. 项目概述

GamlaChain 是一个用 Python 实现的私有区块链教学项目，覆盖区块生成、交易流转、工作量证明 (PoW)、共识算法、REST API 和前端浏览器等完整功能模块。

**技术栈:** Python 3.10+ / FastAPI / Chart.js / Tailwind CSS

---

## 2. 系统架构

```
┌──────────────────────────────────────────────────────┐
│                    Frontend (SPA)                     │
│         Glassmorphism UI / Chart.js / 3s 轮询        │
└──────────────────────┬───────────────────────────────┘
                       │ HTTP REST
┌──────────────────────▼───────────────────────────────┐
│                  API Layer (FastAPI)                  │
│  /chain  /mine  /transactions  /nodes/*  /balance    │
└──────────────────────┬───────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────┐
│                   Core Layer                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │  Block   │  │Transaction│  │   Blockchain     │   │
│  │  - index │  │ - sender  │  │  - chain[]       │   │
│  │  - hash  │  │ - receiver│  │  - pending_txs[] │   │
│  │  - nonce │  │ - amount  │  │  - nodes{}       │   │
│  │  - prev  │  │ - tx_hash │  │  - consensus     │   │
│  └──────────┘  └──────────┘  └──────────────────┘   │
│  ┌──────────┐  ┌──────────────────────────────────┐  │
│  │ Consensus│  │              Wallet               │  │
│  │ - PoW    │  │  - private_key / address / sign   │  │
│  │ - valid  │  └──────────────────────────────────┘  │
│  └──────────┘                                        │
└──────────────────────────────────────────────────────┘
```

---

## 3. 核心数据结构

### 3.1 交易 (Transaction)

```
Transaction
├── sender: str          # 发送方地址
├── receiver: str        # 接收方地址
├── amount: float        # 交易金额
├── timestamp: float     # Unix 时间戳
└── tx_hash: str         # SHA-256(sender + receiver + amount + timestamp)
```

### 3.2 区块 (Block)

```
Block
├── index: int                # 区块高度
├── previous_hash: str        # 前一区块哈希
├── timestamp: float          # 出块时间
├── transactions: list[Transaction]  # 包含的交易列表
├── nonce: int                # PoW 计数器
└── hash: str                 # SHA-256(index + prev_hash + timestamp + txs + nonce)
```

### 3.3 区块链 (Blockchain)

```
Blockchain
├── chain: list[Block]                # 完整链数据
├── pending_transactions: list[Transaction]  # 待打包交易池
├── difficulty: int = 4               # 挖矿难度 (hash 前导零数量)
├── mining_reward: float = 50.0       # 出块奖励
├── nodes: set[str]                   # 邻居节点 netloc 集合
└── node_identifier: str              # 本节点 UUID 标识
```

---

## 4. 共识机制

### 4.1 工作量证明 (Proof of Work)

```
算法流程:
1. 设置 target = "0" × difficulty  (例如 difficulty=4 → "0000")
2. nonce = 0
3. 计算 block.hash = SHA-256(index + prev_hash + timestamp + txs + nonce)
4. 如果 block.hash 以 target 开头 → 完成
5. 否则 nonce += 1, 回到步骤 3
```

**验证:** 接收方仅需一次哈希计算即可验证，满足"难计算、易验证"的核心要求。

### 4.2 最长链共识 (Longest Chain Rule)

```
resolve_conflicts():
  for each neighbour_node:
      获取 neighbour_node 的完整链数据
      如果 邻居链长度 > 本地区块链长度:
          如果 valid_chain(邻居链):
              记录为候选替换链

  如果存在候选替换链:
      用最长候选链替换本地链 → 返回 True
  否则:
      本地区块链为权威链 → 返回 False
```

### 4.3 链验证

`valid_chain(chain)` 接受外部链逐块验证：
1. 每个块的 `previous_hash` 匹配前一个块的 `hash`
2. 每个块的 `hash` 前缀满足难度要求（`difficulty` 个零）
3. 每个块的 `hash` 等于重新计算的哈希值

---

## 5. API 设计

### 5.1 端点总览

| 方法 | 路径 | 功能 | 对应教学 |
|------|------|------|---------|
| GET | `/api/v1/chain` | 返回完整区块链数据 | Step 2 |
| POST | `/api/v1/mine` | 挖矿打包新区块 | Step 2 |
| POST | `/api/v1/transactions` | 创建新交易 | Step 2 |
| GET | `/api/v1/transactions/pending` | 查询待打包交易池 | Step 3 |
| GET | `/api/v1/blocks/latest` | 查询最新区块 | 扩展 |
| GET | `/api/v1/blocks/{index}` | 按高度查询区块 | 扩展 |
| GET | `/api/v1/balance/{address}` | 查询地址余额 | 扩展 |
| GET | `/api/v1/history/{address}` | 查询地址交易历史 | 扩展 |
| GET | `/api/v1/validate` | 校验本地区块链 | 扩展 |
| POST | `/api/v1/nodes/register` | 注册邻居节点 | Step 4 |
| GET | `/api/v1/nodes/resolve` | 触发共识决议 | Step 4 |

### 5.2 统一响应格式

```json
{
  "ok": true,
  "data": { ... },
  "message": "..."
}
```

---

## 6. 模块依赖

```
gamla_chain/
├── __main__.py          → 启动入口 (uvicorn)
├── config.py            → 全局配置 (dataclass)
├── core/
│   ├── block.py          → Block (dataclass)
│   ├── transaction.py    → Transaction (dataclass)
│   ├── chain.py          → Blockchain (dataclass, 核心逻辑)
│   ├── consensus.py      → proof_of_work() / is_valid_proof()
│   ├── wallet.py         → Wallet (地址生成 / 签名)
│   └── blockchain_manager.py → 全局单例
├── api/
│   ├── server.py         → FastAPI 应用实例 + CORS
│   └── routes.py         → 全部 API 路由
└── utils/
    ├── crypto.py          → SHA-256 哈希函数
    └── serializer.py      → JSON 序列化
```

---

## 7. 前端架构

单文件 SPA (`frontend/index.html`)：

```
┌─────────────────────────────────────────────┐
│  Nav Bar  (固定毛玻璃)                        │
├─────────┬───────────┬───────────────────────┤
│ 5 张     │           │                       │
│ 统计卡片  │           │                       │
├─────────┤ 交易模拟器 │  3 张实时图表          │
│ 区块列表 │ +         │  - 出块时间折线图      │
│ (可滚动) │ 待打包池  │  - 区块大小柱状图      │
│         │           │  - 交易数趋势图        │
├─────────┴───────────┴───────────────────────┤
│ TX 池饼图  │  Gas 使用量  │  链信息面板       │
└─────────────────────────────────────────────┘
```

- **数据刷新:** 每 3 秒自动轮询 `/api/v1/chain`
- **图表引擎:** Chart.js 4.x (折线、柱状、环形图)
- **样式:** Tailwind CSS v3 + 自定义 Glassmorphism CSS

---

## 8. 安全与局限

| 项目 | 说明 |
|------|------|
| 密码学 | SHA-256 哈希，非 ECDSA 签名（教学简化） |
| 钱包 | 私钥为随机 hex 字符串，地址为 SHA-256(私钥) |
| 网络 | 节点间 HTTP 明文通信，无 TLS |
| 共识 | 最长链规则，无拜占庭容错 |
| 适用场景 | 教学演示、私有链，不可用于生产环境 |
