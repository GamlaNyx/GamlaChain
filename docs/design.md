# GamlaChain 设计文档

## 1. 项目概述

GamlaChain 是一个用 Python 实现的教学区块链项目。从最初的单节点演示演进为多用户 Web 应用，支持用户注册、钱包管理、转账交易、管理控制台、服务器部署。

**技术栈:** Python 3.10+ / FastAPI / bcrypt / Chart.js / Neumorphism CSS

**在线地址:** http://gamla.cn/gamlachain/

---

## 2. 系统架构

```
┌──────────────────────────────────────────────────────────────┐
│                    Frontend (纯 HTML/CSS/JS)                  │
│  新拟物设计 / Chart.js / 3s 轮询 / SPA 侧边栏导航            │
│  ├── index.html        介绍页                                │
│  ├── login/register    登录注册                              │
│  ├── dashboard.html    用户仪表盘（总览/钱包/转账/记录/水龙头）│
│  └── admin.html        管理控制台（仪表盘/区块链/用户/挖矿）   │
└──────────────────────┬───────────────────────────────────────┘
                       │ HTTP REST (Bearer Token 认证)
┌──────────────────────▼───────────────────────────────────────┐
│                  API Layer (FastAPI)                          │
│  routes.py / routes_auth.py / routes_wallet.py                │
│  routes_admin.py / routes_faucet.py                          │
│  middleware.py (get_current_user / get_admin_user)            │
└──────────────────────┬───────────────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────────────┐
│                   Core Layer                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐           │
│  │  Block   │  │Transaction│  │   Blockchain     │           │
│  └──────────┘  └──────────┘  │  - chain[]        │           │
│  ┌──────────┐  ┌──────────────┐  - pending_txs[]  │           │
│  │ Consensus│  │WalletManager │  - nodes{}        │           │
│  │ - PoW    │  │ - user wallets│  - consensus     │           │
│  └──────────┘  └──────────────┘  └──────────────────┘        │
│  ┌──────────┐  ┌──────────────┐                              │
│  │AuthManager│  │PersistenceMgr│                              │
│  │- bcrypt  │  │ - JSON files │                              │
│  │- session │  └──────────────┘                              │
│  └──────────┘                                                 │
└──────────────────────────────────────────────────────────────┘
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

系统保留地址：`"network"`（矿工奖励）、`"faucet"`（水龙头）。普通交易端点已拦截这些地址。

### 3.2 区块 (Block)

```
Block
├── index: int                    # 区块高度
├── previous_hash: str            # 前一区块哈希
├── timestamp: float              # 出块时间
├── transactions: list[Transaction]  # 交易列表
├── nonce: int                    # PoW 计数器
└── hash: str                     # SHA-256(index + prev_hash + timestamp + txs + nonce)
```

### 3.3 用户 (User)

```
User
├── id: str            # secrets.token_hex(16)
├── username: str      # 登录名 (2-32 字符)
├── password_hash: str # bcrypt(12 rounds)
├── role: str          # "admin" | "user"
└── created_at: float  # 注册时间
```

第一个注册的用户自动获得 `admin` 角色。

### 3.4 Session

```
Session
├── token: str         # secrets.token_hex(16)
├── user_id: str       # 关联 User.id
├── created_at: float
└── expires_at: float  # 7 天后过期
```

---


## 4. 共识机制

### 4.1 工作量证明 (PoW)

```
算法流程:
1. target = "0" × difficulty  (difficulty=4 → "0000")
2. nonce = 0
3. block.hash = SHA-256(index + prev_hash + timestamp + txs + nonce)
4. 如果 block.hash 以 target 开头 → 完成
5. 否则 nonce += 1, 回到步骤 3
```

### 4.2 最长链共识

节点通过 `/nodes/register` 互相注册 → 交易广播到所有节点 → 矿工出块 → 其余节点执行 `/nodes/resolve` 用最长有效链替换本地链。

---

## 5. API 设计

### 5.1 认证方案

- 注册：bcrypt 哈希密码（12 rounds），自动创建首个钱包
- 登录：返回 32 位 hex session token
- 认证：`Authorization: Bearer <token>` Header
- 登出：服务端销毁 session（不仅仅是清除前端 localStorage）
- 速率限制：登录 10次/分钟/IP，注册 5次/分钟/IP

### 5.2 模块化路由

| 路由文件 | 前缀 | 功能 |
|---------|------|------|
| `routes.py` | `/api/v1` | 区块链核心 + 节点管理（部分公开） |
| `routes_auth.py` | `/api/v1/auth` | 用户注册/登录/登出/当前用户 |
| `routes_wallet.py` | `/api/v1/wallet` | 钱包 CRUD + 转账 + 用户目录 |
| `routes_admin.py` | `/api/v1/admin` | 管理仪表盘/链/交易池/用户/挖矿 |
| `routes_faucet.py` | `/api/v1/faucet` | 水龙头状态 + 领取 |

### 5.3 统一响应格式

```json
{
  "ok": true,
  "data": { ... },
  "message": "..."
}
```

---

## 6. 前端设计

### 6.1 新拟物设计系统 (Neumorphism)

```
颜色:
  底色       #f3efe7  (米白)
  阴影暗部   #d5d0c5  (暖灰)
  阴影亮部   #ffffff
  强调色     #5a8a6e  (墨绿)
  成功色     #5a8a6e
  警告色     #c9a96e  (暖金)
  错误色     #c97070  (柔和红)

阴影:
  凸起: 6px 6px 12px #d5d0c5, -6px -6px 12px #fff
  凹陷: inset 4px 4px 8px #d5d0c5, inset -4px -4px 8px #fff

字体:
  标题: DM Sans + Noto Serif SC (思源宋体)
  正文: Inter + Noto Sans SC
  等宽: JetBrains Mono
```

### 6.2 页面架构

```
介绍页 (/index.html)
├── 登录 (/login.html)
│   └── 管理员 → /admin.html
│   └── 普通用户 → /dashboard.html
└── 注册 (/register.html)
    └── 成功后 → /login.html

用户仪表盘 (/dashboard.html) — SPA 侧边栏
├── 总览（余额/交易/钱包统计 + 管理员入口卡片）
├── 我的钱包（列表/创建/显示私钥/复制地址）
├── 转账（发送钱包→接收用户→金额→私钥自动填入）
├── 交易记录（按钱包分组）
└── 水龙头（领取状态/领取按钮）

管理控制台 (/admin.html) — SPA 侧边栏
├── 仪表盘（系统统计）
├── 区块链（iframe 嵌入完整浏览器 — 单/多节点/图表/自动出块/模拟交易）
├── 交易池（待打包交易）
├── 用户管理（用户列表）
└── 挖矿（手动出块）
```

### 6.3 模拟引擎

| 功能 | 行为 |
|------|------|
| ⛏ 自动出块 | 每 2.5 秒在节点 0 挖矿，多节点自动共识同步 |
| 📡 模拟交易 | 5 个测试钱包随机互转（0.08-0.38s 间隔） |

两个功能可独立运行或同时运行。

---

## 7. 安全设计

| 措施 | 实现 |
|------|------|
| 密码存储 | bcrypt，12 rounds salt |
| 登出销毁 Session | 服务端 `_auth_manager.logout(token)` |
| 速率限制 | 登录 10次/分钟/IP，注册 5次/分钟/IP |
| 伪造交易拦截 | `/transactions` 拒绝 `sender="network"/"faucet"` |
| CORS 控制 | 生产环境限制 `CORS_ORIGINS=https://your-domain.com` |
| 非 root 运行 | systemd `User=gamla`，`NoNewPrivileges=yes` |
| 仅本机监听 | `HOST=127.0.0.1`，Nginx 反向代理 |

---

## 8. 数据持久化

```
data/
├── users.json       # 用户列表（含 bcrypt 密码哈希）
├── wallets.json     # 钱包列表（含私钥）
├── sessions.json    # 活跃 Session
├── chain.json       # 区块链数据 + 待打包交易池
└── faucet.json      # 水龙头领取记录
```

每次链状态变化、用户操作后自动保存。启动时自动恢复。

---

## 9. 局限与适用范围

| 项目 | 说明 |
|------|------|
| 密码学 | SHA-256 哈希，简化签名（教学用途，非 ECDSA） |
| 钱包 | 私钥明文存储于服务器（教学简化） |
| 网络 | 节点间 HTTP 明文通信 |
| 共识 | 最长链规则，无拜占庭容错 |
| 适用场景 | 教学演示、内部实验网络，不可用于生产环境 |
