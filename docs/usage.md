# GamlaChain 使用文档

## 1. 环境要求

- **Python** 3.10+
- **pip** 最新版本

推荐使用 conda 虚拟环境 `full_env`（已预装所需依赖）。

---

## 2. 安装

```bash
cd GamlaChain

# 安装依赖
pip install -r requirements.txt

# 或使用 conda 环境
conda activate full_env
```

依赖列表：

| 库 | 用途 |
|----|------|
| fastapi + uvicorn | REST API 框架 |
| pydantic | 数据校验 |
| requests | 节点间 HTTP 通信 |
| cryptography | 密码学扩展（预留） |

---

## 3. 运行演示脚本

无需启动服务器即可体验区块链核心流程：

```bash
python scripts/demo.py
```

输出示例：

```
==================================================
GamlaChain - Blockchain Demo
==================================================

[Wallets]
  Alice  : bbb661bd88a8bca7...
  Bob    : 7815d170b2eb9827...
  Charlie: c24a9dc1c4ffdece...

[Mining genesis reward -> Alice]
  Alice balance: 50.0

[Transactions]
  Added: Alice -> Bob (20), Alice -> Charlie (10), Bob -> Charlie (5)

[Mining block #2 -> Bob]
  Bob balance: 65.0

[Balances]
  Alice  : 20.0
  Bob    : 65.0
  Charlie: 15.0

[Chain Valid?] True
[Block count] 3
...
```

---

## 4. 启动 API 服务器

### 4.1 单节点模式

```bash
python -m gamla_chain
```

服务启动在 `http://127.0.0.1:8000`，自动生成 API 文档：

- Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### 4.2 多节点模式（教学 Step 4 — 共识验证）

在不同终端启动多个节点：

```bash
# 终端 1 — 节点 A (默认端口 8000)
python -m gamla_chain

# 终端 2 — 节点 B
python -m uvicorn gamla_chain.api.server:app --host 127.0.0.1 --port 8001

# 终端 3 — 节点 C (可选，更多节点同理)
python -m uvicorn gamla_chain.api.server:app --host 127.0.0.1 --port 8002
```

### 方式一：通过 curl 操作

```bash
# 节点 A 注册节点 B
curl -X POST http://127.0.0.1:8000/api/v1/nodes/register \
  -H "Content-Type: application/json" \
  -d '{"nodes": ["http://127.0.0.1:8001"]}'

# 在节点 B 上挖 3 个区块
curl -X POST "http://127.0.0.1:8001/api/v1/mine?miner_address=miner_b"
curl -X POST "http://127.0.0.1:8001/api/v1/mine?miner_address=miner_b"
curl -X POST "http://127.0.0.1:8001/api/v1/mine?miner_address=miner_b"

# 在节点 A 上触发共识决议
curl http://127.0.0.1:8000/api/v1/nodes/resolve
```

节点 A 检测到节点 B 的链更长且有效，自动替换：

```json
{
  "ok": true,
  "message": "Our chain was replaced",
  "new_chain": [...]
}
```

### 方式二：通过前端浏览器操作

1. 打开 `frontend/index.html`
2. 切换到 **Multi** 模式
3. 在输入框中添加节点 URL → 点击 **Add**
4. 点击 **Register All (Mesh)** 完成网状注册
5. 在节点 B 的 Mine 按钮挖几个区块
6. 在下拉框选择目标节点 → 点击 **Resolve** 触发共识

---

## 5. API 端点详解

### 5.1 链信息

```bash
# 获取整条链
curl http://127.0.0.1:8000/api/v1/chain

# 获取最新区块
curl http://127.0.0.1:8000/api/v1/blocks/latest

# 获取指定区块
curl http://127.0.0.1:8000/api/v1/blocks/1

# 校验本地区块链
curl http://127.0.0.1:8000/api/v1/validate
```

### 5.2 交易

```bash
# 创建交易
curl -X POST http://127.0.0.1:8000/api/v1/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "0xalice_wallet_address",
    "receiver": "0xbob_wallet_address",
    "amount": 25.5,
    "timestamp": 1700000000.0,
    "tx_hash": ""
  }'

# 查看待打包交易池
curl http://127.0.0.1:8000/api/v1/transactions/pending
```

### 5.3 挖矿

```bash
# 挖矿（miner_address 为奖励接收方）
curl -X POST "http://127.0.0.1:8000/api/v1/mine?miner_address=miner1"
```

### 5.4 查询

```bash
# 查余额
curl http://127.0.0.1:8000/api/v1/balance/0xalice_wallet_address

# 查交易历史
curl http://127.0.0.1:8000/api/v1/history/0xalice_wallet_address
```

### 5.5 共识网络

```bash
# 注册邻居节点
curl -X POST http://127.0.0.1:8000/api/v1/nodes/register \
  -H "Content-Type: application/json" \
  -d '{"nodes": ["http://127.0.0.1:8001", "http://192.168.1.5:5000"]}'

# 触发共识决议
curl http://127.0.0.1:8000/api/v1/nodes/resolve
```

---

## 6. 前端浏览器

### 6.1 启动方式

1. 先启动 API 服务器: `python -m gamla_chain`
2. 浏览器打开 `frontend/index.html`
3. 前端自动连接后端 API（默认 `http://127.0.0.1:8000`），所有数据来自实时 API 调用

### 6.2 单节点模式

默认模式，展示单个节点的完整数据：
- 统计卡片（区块高度、总交易数、难度、待打包池、对等节点数）
- 区块列表（可滚动，点击查看详情）
- 交易发送表单 + 待打包交易池
- 6 个实时图表（出块时间、交易数、区块大小、TX 池饼图、链验证）

### 6.3 多节点模式

切换到 **Multi** 模式，支持 2+ 个节点的监控和共识管理：

| 功能 | 操作 |
|------|------|
| 添加节点 | 输入 URL → 点击 Add |
| 删除节点 | 点击节点标签上的 ✕ |
| Mesh 注册 | 一键 Register All — 所有节点互相注册 |
| 共识决议 | 下拉选择目标节点 → 点击 Resolve |
| 对比统计 | 表格对比各节点高度、交易数、有效性等 |
| 节点详情 | 每个节点独立展示区块列表 + 待打包池 |
| 图表对比 | 前两个节点的出块时间和交易数图表并排 |

### 6.4 操作方式

| 功能 | 操作 |
|------|------|
| 查看区块详情 | 点击任意区块条目 |
| 查看交易详情 | 点击任意待打包交易 |
| 发送交易 | 填写表单 → 点击 Send |
| 挖矿 | 点击 Mine 按钮 |
| 模式切换 | 导航栏 Single / Multi 按钮 |

所有数据每 3 秒自动从后端轮询刷新。

---

## 7. 运行测试

```bash
python -m pytest tests/ -v
```

```
tests/test_chain.py::test_genesis_block PASSED
tests/test_chain.py::test_mine_block PASSED
tests/test_chain.py::test_add_transaction PASSED
tests/test_chain.py::test_balance PASSED
tests/test_chain.py::test_chain_invalid_on_tamper PASSED
tests/test_chain.py::test_valid_chain_accepts_good_chain PASSED
tests/test_chain.py::test_valid_chain_rejects_broken_link PASSED
tests/test_chain.py::test_valid_chain_rejects_invalid_proof PASSED
tests/test_chain.py::test_register_node PASSED
tests/test_chain.py::test_register_node_idempotent PASSED
tests/test_chain.py::test_node_identifier_is_set PASSED
```

---

## 8. 配置

通过环境变量或 `.env` 文件覆盖默认值：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `HOST` | `127.0.0.1` | API 监听地址 |
| `PORT` | `8000` | API 监听端口 |
| `MINING_DIFFICULTY` | `4` | PoW 难度 (hash 前导零个数) |
| `MINING_REWARD` | `50.0` | 出块奖励 (GLC) |

使用方式：

```bash
# Linux/Mac
export PORT=9000 MINING_DIFFICULTY=5
python -m gamla_chain

# Windows CMD
set PORT=9000 && set MINING_DIFFICULTY=5 && python -m gamla_chain
```

---

## 9. 项目结构速查

```
GamlaChain/
├── gamla_chain/              # 主包
│   ├── core/                 #   区块链核心模块
│   ├── api/                  #   REST API 层
│   ├── utils/                #   工具函数 (hash, 序列化)
│   ├── config.py             #   全局配置
│   └── __main__.py           #   启动入口
├── frontend/
│   └── index.html            #   区块链浏览器 SPA (实时 API 数据)
├── scripts/
│   └── demo.py               #   命令行演示脚本
├── tests/
│   └── test_chain.py         #   11 项单元测试
├── docs/
│   ├── design.md             #   设计文档
│   ├── usage.md              #   使用文档 (本文件)
│   └── reference/            #   教学参考材料
├── README.md                 #   项目说明
├── LICENSE                   #   MIT 开源协议
├── requirements.txt
├── pyproject.toml
└── .env.example
```
