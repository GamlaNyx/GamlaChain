# GamlaChain 公网部署设计文档

**日期:** 2026-06-14
**版本:** 1.0
**场景:** 教学演示 — 部署到服务器，他人可注册钱包并相互交易

---

## 1. 部署目标

- 场景：教学演示
- 部署方式：服务器直接运行（`python -m gamla_chain` + systemd 守护）
- 持久化：JSON 文件定期保存 + 启动时恢复
- 钱包模式：服务器托管钱包，用户名+密码登录后管理

---

## 2. 整体架构

```
用户浏览器                    服务器
┌─────────────────┐          ┌──────────────────────┐
│  介绍页 (首页)    │          │  FastAPI Server       │
│  ├ 注册/登录      │  HTTP    │  ├ /api/v1/auth/*     │  认证
│  └ 进入仪表盘     │────────→ │  ├ /api/v1/wallet/*   │  钱包
│                  │          │  ├ /api/v1/chain/*    │  链信息(公开)
│  用户仪表盘       │          │  ├ /api/v1/admin/*    │  管理端
│  ├ 侧边栏导航     │          │  └ /api/v1/trans...*  │  交易
│  ├ 钱包概览       │          │                      │
│  ├ 转账           │          │  持久化层              │
│  └ 交易历史       │          │  ├ data/chain.json    │
│                  │          │  ├ data/users.json    │
│  管理员控制台      │          │  ├ data/sessions.json │
│  └ 原区块链浏览器  │          │  └ data/wallets.json  │
└─────────────────┘          └──────────────────────┘
```

---

## 3. 后端设计

### 3.1 新增依赖

- `bcrypt` (密码哈希，唯一新增依赖)
- `python-multipart` (表单数据解析，FastAPI 可选依赖)

### 3.2 数据模型与持久化

| 模型 | 文件 | 字段 |
|------|------|------|
| User | data/users.json | id, username, password_hash, role(user/admin), created_at |
| Wallet | data/wallets.json | address, private_key, user_id, label, created_at |
| Session | data/sessions.json | token(uuid), user_id, created_at, expires_at |
| Chain | data/chain.json | 完整区块链数据 + pending_transactions |

持久化策略：
- 链数据：每次区块变动后异步保存
- 用户/钱包/会话：每次变更后立即同步保存
- 启动时自动从 JSON 文件恢复所有数据

### 3.3 API 端点

**公开端点（无需登录）：**
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v1/auth/register | 注册（自动创建首个钱包） |
| POST | /api/v1/auth/login | 登录，返回 session token |
| GET | /api/v1/chain/info | 公开链信息摘要 |

**用户端点（需要 session token）：**
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v1/auth/logout | 登出 |
| GET | /api/v1/auth/me | 当前用户信息 + 钱包列表 |
| POST | /api/v1/wallet/create | 创建新钱包 |
| GET | /api/v1/wallet/list | 我的钱包列表 |
| GET | /api/v1/wallet/{addr}/balance | 查余额 |
| GET | /api/v1/wallet/{addr}/history | 交易历史 |
| POST | /api/v1/transactions | 发送交易 |

**管理员端点（需要 session token + role=admin）：**
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/admin/dashboard | 管理员仪表盘数据 |
| GET | /api/v1/admin/chain | 完整区块链 |
| GET | /api/v1/admin/pending | 待打包交易池 |
| POST | /api/v1/admin/mine | 手动挖矿 |
| GET | /api/v1/admin/users | 用户列表 |

**保留原有端点（兼容旧前端）：**
原有的 /api/v1/chain, /api/v1/mine 等端点保持不变（管理员使用）

### 3.4 认证中间件

- Header: `Authorization: Bearer <session_token>`
- FastAPI `Depends(get_current_user)` 依赖函数验证 session
- `Depends(get_admin_user)` 额外检查 role=admin

---

## 4. 前端设计 — 新拟物 (Neumorphism)

### 4.1 设计系统

**颜色：**
- 底色 `#e8ecf1`，凸起亮面 `#eef1f5`，阴影 `#c4cad3`
- 主文字 `#2d3748`，辅文字 `#718096`
- 强调色 `#5b7fff`，成功色 `#68b984`

**阴影规则（新拟物核心）：**
- 凸起元素: `box-shadow: 6px 6px 12px #c4cad3, -6px -6px 12px #ffffff`
- 凹陷元素: `box-shadow: inset 4px 4px 8px #c4cad3, inset -4px -4px 8px #ffffff`
- 选中/激活: 凹陷阴影 + 微深背景

**字体：**
- 标题: DM Sans + PingFang SC
- 正文: Inter + PingFang SC
- 数据: JetBrains Mono

### 4.2 页面结构

```
/               介绍页 (公开)
/login          登录页
/register       注册页
/dashboard      用户仪表盘 (需登录)
  ├ 总览        (概览卡片: 余额、交易数、钱包数)
  ├ 我的钱包    (钱包列表、创建钱包、查看私钥)
  ├ 转账        (选择发送钱包 → 输入接收地址 → 输入金额)
  └ 交易记录    (交易历史列表)
/admin          管理员控制台 (需登录 + admin)
  ├ 仪表盘      (链高度、难度、节点数等统计)
  ├ 区块链      (原 GamlaChain 浏览器，暗色玻璃拟态)
  ├ 用户管理    (用户列表)
  └ 挖矿        (手动挖矿控制)
```

### 4.3 技术选型

- 纯 HTML/CSS/JS（无框架，与现有项目一致）
- 通过 URL hash 实现前端路由：`#dashboard`, `#admin` 等
- 每个页面独立 HTML 文件或单文件 SPA（视复杂度决定）

---

## 5. 文件结构变更

```
GamlaChain/
├── gamla_chain/
│   ├── core/
│   │   ├── auth.py           # NEW: 用户认证 + session 管理
│   │   ├── persistence.py    # NEW: JSON 文件持久化
│   │   ├── chain.py          # MODIFIED: 集成持久化
│   │   └── ...
│   ├── api/
│   │   ├── routes.py         # MODIFIED: 新增 auth/wallet/admin 路由
│   │   ├── routes_auth.py    # NEW: 认证相关路由
│   │   ├── routes_wallet.py  # NEW: 钱包相关路由
│   │   ├── routes_admin.py   # NEW: 管理员路由
│   │   ├── middleware.py     # NEW: 认证中间件 (Depends)
│   │   └── server.py         # MODIFIED: 注册新路由
│   └── ...
├── frontend/
│   ├── index.html            # REPURPOSED: 介绍页
│   ├── dashboard.html        # NEW: 用户仪表盘 (新拟物)
│   ├── admin.html            # REPURPOSED: 管理员控制台 (原有暗色)
│   └── css/
│       └── neumorphism.css   # NEW: 新拟物样式系统
├── data/                     # NEW: 持久化数据目录
└── ...
```

---

## 6. 安全考虑

- 密码 bcrypt 哈希，12 轮 salt
- Session token 用 uuid4，7 天过期
- 私钥明文存储于服务器（教学场景，生产环境应加密）
- 无 HTTPS（教学部署简化，生产需 nginx 反向代理 + Let's Encrypt）

---

## 7. 部署步骤

1. 服务器安装 Python 3.10+
2. `pip install -r requirements.txt`
3. 配置环境变量（HOST, PORT 等）
4. systemd service 配置守护进程
5. 可选：nginx 反向代理 + 静态文件服务

---
