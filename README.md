# GamlaChain

基于 Python 的区块链教学项目。遵循 [Learn Blockchains by Building One](https://hackernoon.com/learn-blockchains-by-building-one) 教程构建，并扩展了多用户系统、钱包管理、新拟物前端、管理控制台等完整功能。

**在线地址：** http://gamla.cn/gamlachain/

## 功能特性

- **区块链核心** — Block、Transaction、SHA-256 哈希、PoW 工作量证明
- **多用户系统** — 注册/登录（bcrypt 密码哈希）、Session 认证、角色管理
- **钱包管理** — 创建钱包、余额查询、转账交易、交易历史、私钥管理
- **水龙头** — 每用户可领取 3 次 × 10 GLC 测试币
- **用户目录** — 转账时选择其他用户的主钱包地址
- **共识算法** — 最长链规则 + 多节点网状网络 + 自动同步
- **REST API** — 20+ 个 FastAPI 端点，速率限制、CORS 控制
- **管理控制台** — 系统概览、区块链浏览器（单/多节点、Chart.js 图表）、用户管理、手动挖矿
- **新拟物设计** — 米白色背景 + 墨绿色强调，统一风格
- **安全加固** — 登出销毁 Session、伪造交易拦截、速率限制
- **数据持久化** — JSON 文件存储，服务重启数据不丢失
- **服务器部署** — systemd 守护 + Nginx 反向代理，完整部署文档

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务器
python -m gamla_chain
# → http://127.0.0.1:8000

# 浏览器打开 http://127.0.0.1:8000
# 第一个注册的用户自动成为管理员
```

## 用户角色

| 角色 | 权限 |
|------|------|
| **管理员** | 管理控制台、查看区块链、用户管理、手动挖矿、自动出块、模拟交易 |
| **普通用户** | 钱包管理、转账、水龙头领币、交易记录查询 |

## 项目结构

```
GamlaChain/
├── gamla_chain/              # Python 后端
│   ├── core/                 #   区块链核心
│   │   ├── auth.py           #     用户认证 + Session 管理
│   │   ├── block.py          #     区块数据结构
│   │   ├── chain.py          #     区块链主类 + 共识
│   │   ├── consensus.py      #     工作量证明 (PoW)
│   │   ├── persistence.py    #     JSON 文件持久化
│   │   ├── transaction.py    #     交易数据结构
│   │   ├── wallet.py         #     简易钱包（底层）
│   │   ├── wallet_manager.py #     用户钱包管理
│   │   └── blockchain_manager.py # 全局单例
│   ├── api/                  #   REST API 层
│   │   ├── server.py         #     FastAPI 应用 + CORS
│   │   ├── middleware.py     #     认证中间件
│   │   ├── routes.py         #     区块链/节点 API
│   │   ├── routes_auth.py    #     注册/登录 API
│   │   ├── routes_wallet.py  #     钱包/转账/用户目录 API
│   │   ├── routes_admin.py   #     管理端 API
│   │   └── routes_faucet.py  #     水龙头 API
│   ├── utils/                #   工具模块
│   │   ├── crypto.py         #     SHA-256 哈希
│   │   ├── rate_limiter.py   #     速率限制
│   │   └── serializer.py     #     JSON 序列化
│   ├── config.py             #   全局配置
│   └── __main__.py           #   启动入口
├── frontend/                 # 纯 HTML/CSS/JS
│   ├── css/neumorphism.css   #   新拟物设计系统
│   ├── index.html            #   介绍页
│   ├── login.html            #   登录页
│   ├── register.html         #   注册页
│   ├── dashboard.html        #   用户仪表盘 SPA
│   ├── admin.html            #   管理员控制台
│   └── original_explorer.html#   区块链浏览器 (iframe)
├── deploy/                   # 部署配置
│   ├── gamlachain.service    #   systemd 单元文件
│   └── README.md             #   完整部署文档
├── tests/                    # 39 项测试
├── docs/                     # 文档
├── requirements.txt
└── pyproject.toml
```

## 配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `HOST` | `127.0.0.1` | API 监听地址 |
| `PORT` | `8000` | API 端口 |
| `MINING_DIFFICULTY` | `4` | PoW 难度 |
| `MINING_REWARD` | `50.0` | 出块奖励 (GLC) |
| `CORS_ORIGINS` | `*` | 跨域来源 |
| `SECRET_KEY` | 自动生成 | 安全密钥 |
| `DATA_DIR` | `data` | 数据目录 |

## 测试

```bash
python -m pytest tests/ -v
# 39 项测试全部通过
```

## 部署

详见 `deploy/README.md` — 包含服务器初始化、systemd、Nginx、HTTPS、防火墙完整步骤。

## License

MIT — 详见 [LICENSE](LICENSE)
