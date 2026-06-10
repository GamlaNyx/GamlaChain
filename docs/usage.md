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

---

## 4. 启动 API 服务器

### 4.1 单节点模式

```bash
python -m gamla_chain
```

服务启动在 `http://127.0.0.1:8000`，自动生成 API 文档：

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

### 4.2 多节点模式（教学 Step 4 — 共识验证）

在不同终端启动多个节点：

```bash
# 终端 1 — 节点 A (矿工, 端口 8000)
python -m gamla_chain

# 终端 2 — 节点 B (同步节点, 端口 8001)
python -m uvicorn gamla_chain.api.server:app --host 127.0.0.1 --port 8001

# 终端 3 — 节点 C (端口 8002，可选)
python -m uvicorn gamla_chain.api.server:app --host 127.0.0.1 --port 8002
```

#### 方式一：通过 curl 手动操作

```bash
# 1. 互相注册
curl -X POST http://127.0.0.1:8000/api/v1/nodes/register \
  -H "Content-Type: application/json" \
  -d '{"nodes": ["http://127.0.0.1:8001"]}'

curl -X POST http://127.0.0.1:8001/api/v1/nodes/register \
  -H "Content-Type: application/json" \
  -d '{"nodes": ["http://127.0.0.1:8000"]}'

# 2. 在节点 A 上发送交易 + 挖矿
curl -X POST http://127.0.0.1:8000/api/v1/transactions \
  -H "Content-Type: application/json" \
  -d '{"sender":"alice","receiver":"bob","amount":25.0,"timestamp":1700000000,"tx_hash":""}'

curl -X POST "http://127.0.0.1:8000/api/v1/mine?miner_address=miner"

# 3. 节点 B 同步
curl http://127.0.0.1:8001/api/v1/nodes/resolve
```

节点 B 检测到节点 A 的链更长，自动替换：

```json
{
  "ok": true,
  "message": "Our chain was replaced",
  "new_chain": [...]
}
```

#### 方式二：通过前端自动模拟

1. 打开 `frontend/index.html`
2. 切换到 **多节点** 模式
3. 添加节点 URL → 点击 **模拟交易**
4. 自动完成：Mesh 注册 → TX 广播到所有节点 → 节点 0 挖矿 → 其余节点自动共识同步
5. 状态栏显示同步计数：`12 TX | 5 blk | 27s | ↻8`

**模拟逻辑说明：**
- 交易：同一笔 TX 同时广播到所有节点
- 挖矿：仅节点 0 出块（模拟单一矿工）
- 出块后：自动在所有其余节点触发 `/nodes/resolve` 共识同步
- 结果：所有节点维护同一条链的副本（真实区块链行为）

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

# 触发共识决议（用最长有效链替换本地链）
curl http://127.0.0.1:8000/api/v1/nodes/resolve
```

---

## 6. 前端浏览器

### 6.1 启动方式

1. 先启动 API 服务器: `python -m gamla_chain`
2. 浏览器打开 `frontend/index.html`
3. 前端自动连接后端 API（默认 `http://127.0.0.1:8000`）

### 6.2 单节点模式

默认模式，展示单个节点的完整数据：

| 区域 | 内容 |
|------|------|
| 统计卡片 | 区块高度(含增量)、总交易数、挖矿难度、待打包池、流通总量 |
| 区块列表 | 搜索栏 + 可滚动列表，点击查看详情，新区块青色辉光 |
| 发起交易 | 发送方/接收方/金额 + 随机填充按钮 |
| 可视化 | 区块链卡片式展示（最后 7 个区块），显示高度、哈希、TX 数、nonce |
| 待打包交易 | 交易池列表，点击查看详情 |
| 图表(右列) | 出块时间、每块交易数、区块大小（3 个时序图表） |
| 底部 | 交易池饼图、链有效性、地址浏览器（查余额+历史） |
| 链信息栏 | 链 ID、共识、节点、奖励、平均出块、对等节点 |

### 6.3 多节点模式

切换到 **多节点** 模式，支持 2+ 个节点：

| 功能 | 操作 |
|------|------|
| 添加节点 | 输入 URL → 点击 Add |
| 删除节点 | 点击节点标签上的 ✕ |
| 全部注册 | 一键 Register All (Mesh) — 所有节点互相注册 |
| 共识决议 | 下拉选择目标节点 → 点击 Resolve |
| 模拟交易 | 自动 Mesh 注册 → TX 广播所有节点 → 节点 0 挖矿 → 自动共识同步 |
| 区块链可视化 | 每个节点一行，展示该节点的区块链 |
| 对比统计 | 表格对比各节点高度、交易数、有效性等 |
| 节点详情 | 每个节点独立展示区块列表 + 待打包池 |
| 图表对比 | 最多 4 个节点的出块时间和交易数图表 |

### 6.4 快捷键

| 功能 | 操作 |
|------|------|
| 查看区块详情 | 点击任意区块条目 / 可视化区块卡片 |
| 查看交易详情 | 点击任意待打包交易 |
| 发送交易 | 填写表单 → 点击发送 (Enter 快捷发送) |
| 挖矿 | 点击 Mine 按钮 |
| 随机填充 | 点击 TX 表单的随机按钮 |
| 模式切换 | 导航栏 单节点 / 多节点 |
| 搜索 | 区块列表顶部的搜索框 (#区块号 或 0x地址) |

所有数据每 3 秒自动从后端轮询刷新。

---

## 7. 运行测试

```bash
python -m pytest tests/ -v
```

共 11 项测试：chain, transaction, balance, consensus, validation, node registration

---

## 8. 配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `HOST` | `127.0.0.1` | API 监听地址 |
| `PORT` | `8000` | API 监听端口 |
| `MINING_DIFFICULTY` | `4` | PoW 难度 (前导零个数) |
| `MINING_REWARD` | `50.0` | 出块奖励 (GLC) |

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
│   └── index.html            #   区块链浏览器 SPA (1052 行, 中文界面)
├── scripts/
│   └── demo.py               #   命令行演示脚本
├── tests/
│   └── test_chain.py         #   11 项单元测试
├── docs/
│   ├── design.md             #   设计文档
│   ├── usage.md              #   使用文档 (本文件)
│   └── reference/            #   教学参考材料 (gitignored)
├── README.md                 #   项目说明
├── LICENSE                   #   MIT 开源协议
├── requirements.txt
├── pyproject.toml
└── .env.example
```
