# GamlaChain 开发者指南

## 1. 项目总览

```
GamlaChain/
├── gamla_chain/                         # Python 后端
│   ├── core/                            #   核心逻辑
│   │   ├── auth.py                      #     用户认证 + Session 管理
│   │   ├── block.py                     #     区块数据结构
│   │   ├── blockchain_manager.py        #     全局区块链单例
│   │   ├── chain.py                     #     区块链主类 + 共识
│   │   ├── consensus.py                 #     工作量证明 (PoW)
│   │   ├── persistence.py               #     JSON 文件持久化
│   │   ├── transaction.py               #     交易数据结构
│   │   ├── wallet.py                    #     底层钱包 (SHA-256)
│   │   └── wallet_manager.py            #     用户钱包管理
│   ├── api/                             #   REST API
│   │   ├── middleware.py                #     认证中间件 (Depends)
│   │   ├── routes.py                    #     区块链/节点 API
│   │   ├── routes_admin.py              #     管理员 API
│   │   ├── routes_auth.py               #     认证 API
│   │   ├── routes_faucet.py             #     水龙头 API
│   │   ├── routes_wallet.py             #     钱包/转账/用户目录 API
│   │   └── server.py                    #     FastAPI 应用工厂
│   ├── utils/                           #   工具
│   │   ├── crypto.py                    #     SHA-256 哈希
│   │   ├── rate_limiter.py              #     速率限制
│   │   └── serializer.py               #     JSON 序列化
│   ├── config.py                        #   配置管理
│   └── __main__.py                      #   启动入口
├── frontend/                            # 纯 HTML/CSS/JS
│   ├── css/neumorphism.css              #   新拟物设计系统
│   ├── index.html                       #   介绍页
│   ├── login.html                       #   登录页
│   ├── register.html                    #   注册页
│   ├── dashboard.html                   #   用户仪表盘 SPA
│   ├── admin.html                       #   管理控制台
│   └── original_explorer.html           #   区块链浏览器 (iframe 嵌入)
├── deploy/                              # 部署
│   ├── gamlachain.service               #   systemd 单元
│   └── README.md                        #   部署文档
├── tests/                               # 39 项测试
├── docs/                                # 文档
├── requirements.txt
└── pyproject.toml
```

---

## 2. 启动流程

```
__main__.py main()
├── Config.from_env()              → 读取环境变量
├── PersistenceManager(data_dir)   → 初始化持久化层
├── AuthManager(persistence)       → 加载用户 + Session
├── WalletManager(persistence)     → 加载钱包
├── 恢复链数据 (persistence.load)
├── blockchain.set_persist_callback(chain_persist)
├── init_auth_middleware(auth)
├── init_*_routes(...)             → 注入模块依赖
├── create_app(config)             → FastAPI 应用
│   ├── 注册所有路由
│   ├── CORS (可配置)
│   └── 挂载静态文件
└── uvicorn.run(app)
```

---

## 3. 核心模块详解

### 3.1 AuthManager (`core/auth.py`)

```
AuthManager
├── users: dict[str, User]          # username → User
├── sessions: dict[str, Session]    # token → Session
├── register(username, password)    → User (bcrypt 12 rounds)
│   └── 第一个用户自动 admin
├── login(username, password)       → Session | None
│   └── 验证 bcrypt → 创建 32 位 hex token
├── logout(token)                   → None
│   └── 服务端销毁 session（非仅前端清除）
├── get_user_by_token(token)        → User | None
│   └── 检查过期 → 自动清理过期 session
└── _load() / _save_users() / _save_sessions()
    └── JSON 持久化
```

### 3.2 WalletManager (`core/wallet_manager.py`)

```
WalletManager
├── wallets: dict[str, dict]      # address → wallet
├── _generate_wallet()             → (private_key, address)
│   └── SHA-256(private_key) = address
├── create_wallet(user_id, label) → wallet dict
├── get_user_wallets(user_id)     → list[dict]
├── get_wallet_by_address(addr)   → dict | None
└── _load() / _save()
```

### 3.3 PersistenceManager (`core/persistence.py`)

```
PersistenceManager
├── save(name, data)         → 原子写入 (tmp → rename)
├── load(name)               → data | None
└── data_dir 自动创建
```

### 3.4 Blockchain (`core/chain.py`)

已扩展持久化钩子：

```
Blockchain (新增字段)
└── _persist_callback        → 链变更后自动回调

变更触发点:
├── add_transaction()        → _notify_persist()
├── mine_pending_transactions() → _notify_persist()
└── resolve_conflicts()      → 替换链后 _notify_persist()
```

### 3.5 Rate Limiter (`utils/rate_limiter.py`)

```
RateLimiter
├── requests: int             # 窗口内最大请求数
├── window: int               # 时间窗口 (秒)
├── is_allowed(ip) → bool    # 滑动窗口判断
└── get_client_ip(request)    # X-Forwarded-For 优先

预建实例:
├── login_limiter:    10 req/min
├── register_limiter:  5 req/min
└── faucet_limiter:    3 req/min
```

---

## 4. 认证中间件 (`api/middleware.py`)

```python
# 依赖注入
async def get_current_user(authorization: Header) → User
    # 1. 提取 Bearer token
    # 2. AuthManager.get_user_by_token(token)
    # 3. 返回 User 或 401

async def get_admin_user(authorization: Header) → User
    # 同上 + role == "admin" 检查，否则 403
```

---

## 5. API 路由模块化

每个路由文件使用模块级全局变量持有依赖引用，通过 `init_*_routes()` 在启动时注入：

```python
# routes_auth.py
_auth_manager = None
_wallet_manager = None

def init_auth_routes(auth_manager, wallet_manager):
    global _auth_manager, _wallet_manager
    _auth_manager = auth_manager
    _wallet_manager = wallet_manager
```

---

## 6. 前端架构

### 6.1 技术选型

- 纯 HTML/CSS/JS，零构建步骤
- 共享 `neumorphism.css` 设计系统（CSS 变量 + 阴影系统）
- Google Fonts CDN（Inter、DM Sans、JetBrains Mono、Noto Serif SC、Noto Sans SC）
- Font Awesome 6.5.1 CDN（图标）
- Chart.js 4.4.7 CDN（管理控制台图表）
- localStorage 存储 auth token 和用户名/角色
- `file://` 协议自动检测，fallback 到 `http://127.0.0.1:8000`

### 6.2 页面通信

所有 API 调用使用 `window.location.origin`（或 `file://` fallback）作为 API 基础 URL：

```javascript
const API = window.location.protocol === 'file:'
  ? 'http://127.0.0.1:8000'
  : window.location.origin;

async function api(method, path, body) {
  const res = await fetch(API + path, {
    method,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer ' + TOKEN
    },
    body: body ? JSON.stringify(body) : undefined
  });
  if (res.status === 401) {
    localStorage.clear();
    window.location.href = 'login.html';
  }
  return res.json();
}
```

### 6.3 会话管理

```
登录成功
├── localStorage.setItem('gamla_token', token)
├── localStorage.setItem('gamla_username', username)
└── localStorage.setItem('gamla_role', role)

登出
├── POST /api/v1/auth/logout (服务端销毁)
├── localStorage.clear()
└── window.location.href = 'index.html'

401 响应
├── localStorage.clear()
└── window.location.href = 'login.html'
```

### 6.4 水龙头流程

```
loadFaucet()
├── GET /api/v1/faucet/info → 显示已领取/剩余次数
├── GET /api/v1/auth/me → 填充钱包下拉框
└── 重置按钮状态 (btn.innerHTML = 原始文本)

claimFaucet()
├── 验证钱包
├── POST /api/v1/faucet/claim {wallet_address}
├── 成功 → 显示 TX hash → toast → loadFaucet() (重置按钮)
└── 失败 → 显示错误 → 恢复按钮
```

### 6.5 转账私钥自动填入

```
option value = "地址|私钥"
  ↓ 选择钱包时
onSenderWalletChange()
  → value.split('|')[1] → 填入 txPrivateKey
```

---

## 7. 测试

39 项测试，分类：

| 模块 | 数量 | 覆盖内容 |
|------|------|---------|
| `test_chain.py` | 11 | 创世块、挖矿、交易、余额、链验证、共识、节点注册 |
| `test_auth.py` | 10 | 注册、登录、密码验证、Session 管理、角色分配、持久化 |
| `test_persistence.py` | 5 | 保存/加载/文件创建/列表/目录自动创建 |
| `test_wallet_manager.py` | 6 | 创建钱包/标签/用户隔离/地址查找/持久化 |
| `test_integration.py` | 7 | 端到端：注册→登录→获取信息→余额→创建第二钱包→admin 拦截→链信息 |

```bash
python -m pytest tests/ -v     # 全部通过
```

---

## 8. 安全

| 措施 | 位置 |
|------|------|
| bcrypt 密码哈希 (12 rounds) | `auth.py:register()` |
| 登出服务端销毁 Session | `routes_auth.py:logout()` |
| 伪造交易拦截 (network/faucet) | `routes.py:create_transaction()` |
| 速率限制 | `rate_limiter.py` → `routes_auth.py` |
| 可配置 CORS | `config.py` → `server.py` |
| 非 root 运行 | `gamlachain.service` |
| 仅本机监听 | `HOST=127.0.0.1` |

---

## 9. 持久化策略

| 事件 | 触发保存 |
|------|---------|
| 用户注册/登录/登出 | `_save_users()` / `_save_sessions()` |
| 钱包创建 | `_save()` |
| 交易加入待打包池 | `_notify_persist()` |
| 挖矿出块 | `_notify_persist()` |
| 共识替换链 | `_notify_persist()` |
| 水龙头领取 | `_save_claims()` |
