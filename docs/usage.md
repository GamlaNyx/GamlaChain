# GamlaChain 使用文档

## 1. 环境要求

- **Python** 3.10+
- **pip** 最新版本

---

## 2. 安装

```bash
cd GamlaChain
pip install -r requirements.txt
```

依赖列表：

| 库 | 用途 |
|----|------|
| fastapi + uvicorn | REST API 框架 |
| pydantic | 数据校验 |
| bcrypt | 密码哈希 |
| requests | 节点间 HTTP 通信 |

---

## 3. 启动服务器

```bash
python -m gamla_chain
```

服务启动在 `http://127.0.0.1:8000`。

### 本地直接打开（无需服务器）

双击 `frontend/index.html` 即可浏览介绍页。注册/登录等需要 API 的功能会自动连接到 `http://127.0.0.1:8000`（需先启动服务器）。

---

## 4. 用户使用流程

### 4.1 注册账户

1. 打开 `http://127.0.0.1:8000` → 点击「注册」
2. 填写用户名（2-32 字符）和密码（4-128 字符）
3. 注册成功后自动跳转登录页
4. **第一个注册的用户自动成为管理员**

### 4.2 登录

登录后根据角色跳转：
- **普通用户** → 用户仪表盘 `/dashboard.html`
- **管理员** → 管理员控制台 `/admin.html`

### 4.3 用户仪表盘

| 页面 | 功能 |
|------|------|
| **总览** | 总余额、交易次数、钱包数量、最近交易、管理员入口（仅管理员可见） |
| **我的钱包** | 查看/创建钱包，显示私钥（点👁）、复制地址 |
| **转账** | 选择发送钱包 → 选择接收用户（自动填入地址）→ 输入金额 → 私钥自动填入 → 确认 |
| **交易记录** | 按钱包查看收支历史 |
| **水龙头** | 每用户可领取 3 次，每次 10 GLC |

### 4.4 管理员控制台

| 页面 | 功能 |
|------|------|
| **仪表盘** | 区块高度、总交易数、流通总量、用户数、钱包数 |
| **区块链** | 完整区块链浏览器 — 单/多节点切换、区块列表、Chart.js 图表、地址查询、自动出块、模拟交易 |
| **交易池** | 待打包交易列表 |
| **用户管理** | 注册用户列表 |
| **挖矿** | 手动挖矿出块 |

---

## 5. 常用操作

### 转账流程

1. 进入「转账」页面
2. 选择发送钱包（私钥自动填入）
3. 在「接收方」下拉框选择目标用户（自动填入其主钱包地址），或手动输入地址
4. 输入金额 → 点击「确认转账」
5. 交易进入待打包池，管理员挖矿后到账

### 水龙头领币

1. 进入「水龙头」页面
2. 选择接收钱包 → 点击「领取 10 GLC」
3. 交易以 `faucet` 为发送方加入交易池
4. 管理员挖矿后到账

### 模拟交易（管理员）

在管理控制台 → 区块链页面：

| 按钮 | 功能 |
|------|------|
| ⛏ **自动出块** | 每 2.5 秒自动挖矿出块，多节点模式自动共识同步 |
| 📡 **模拟交易** | 5 个测试钱包（alice/bob/charlie/dave/eve）随机相互转账 |

---

## 6. API 端点

### 公开端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/auth/register` | 用户注册 |
| POST | `/api/v1/auth/login` | 用户登录 |
| GET | `/api/v1/chain/info` | 链信息摘要 |
| GET | `/api/v1/chain` | 完整区块链 |
| GET | `/api/v1/blocks/latest` | 最新区块 |
| GET | `/api/v1/blocks/{index}` | 按高度查区块 |
| POST | `/api/v1/transactions` | 创建交易（系统地址已拦截） |
| GET | `/api/v1/transactions/pending` | 待打包交易池 |
| POST | `/api/v1/mine` | 挖矿出块 |
| GET | `/api/v1/balance/{address}` | 地址余额 |
| GET | `/api/v1/history/{address}` | 地址交易历史 |
| GET | `/api/v1/validate` | 校验区块链 |
| POST | `/api/v1/nodes/register` | 注册邻居节点 |
| GET | `/api/v1/nodes/resolve` | 触发共识决议 |

### 需认证端点（Header: `Authorization: Bearer <token>`）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/auth/logout` | 登出（销毁 Session） |
| GET | `/api/v1/auth/me` | 当前用户信息 + 钱包列表（含私钥） |
| POST | `/api/v1/wallet/create` | 创建新钱包 |
| GET | `/api/v1/wallet/list` | 钱包列表 |
| GET | `/api/v1/wallet/{addr}/balance` | 查余额 |
| GET | `/api/v1/wallet/{addr}/history` | 交易历史 |
| POST | `/api/v1/wallet/send` | 发送交易（验证所有权+余额） |
| GET | `/api/v1/wallet/directory` | 用户目录（转账用） |
| GET | `/api/v1/faucet/info` | 水龙头状态 |
| POST | `/api/v1/faucet/claim` | 领取代币 |

### 管理员端点（需 admin 角色）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/admin/dashboard` | 管理仪表盘 |
| GET | `/api/v1/admin/chain` | 完整区块链 |
| GET | `/api/v1/admin/pending` | 待打包交易池 |
| POST | `/api/v1/admin/mine` | 手动挖矿 |
| GET | `/api/v1/admin/users` | 用户列表 |

---

## 7. 多节点共识

```bash
# 终端 1 — 节点 A
python -m gamla_chain

# 终端 2 — 节点 B
python -m uvicorn gamla_chain.api.server:app --port 8001

# 互相注册
curl -X POST http://127.0.0.1:8000/api/v1/nodes/register \
  -H "Content-Type: application/json" \
  -d '{"nodes": ["http://127.0.0.1:8001"]}'

curl -X POST http://127.0.0.1:8001/api/v1/nodes/register \
  -H "Content-Type: application/json" \
  -d '{"nodes": ["http://127.0.0.1:8000"]}'

# 节点 A 挖矿 → 节点 B 同步
curl -X POST "http://127.0.0.1:8000/api/v1/mine?miner_address=miner"
curl http://127.0.0.1:8001/api/v1/nodes/resolve
```

---

## 8. 运行测试

```bash
python -m pytest tests/ -v
```

共 39 项测试：chain (11)、auth (10)、persistence (5)、wallet_manager (6)、integration (7)

---

## 9. 配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `HOST` | `127.0.0.1` | API 监听地址 |
| `PORT` | `8000` | API 端口 |
| `MINING_DIFFICULTY` | `4` | PoW 难度 |
| `MINING_REWARD` | `50.0` | 出块奖励 (GLC) |
| `CORS_ORIGINS` | `*` | 跨域来源 |
| `SECRET_KEY` | 自动生成 | 安全密钥 |
| `DATA_DIR` | `data` | 数据目录 |
