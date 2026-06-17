# GamlaChain 生产环境部署指南

> 适用系统：Ubuntu 20.04+ / Debian 11+  
> 最终效果：`https://your-domain.com` — 全站 HTTPS，Nginx 反向代理，防火墙仅开放 22/80/443

---

## 一、服务器最低配置

| 项目 | 最低 | 推荐 |
|------|------|------|
| CPU | 1 核 | 2 核 |
| 内存 | 512 MB | 1 GB |
| 磁盘 | 2 GB | 10 GB |
| 系统 | Ubuntu 20.04 | Ubuntu 22.04 |
| 网络 | 公网 IP | 公网 IP + 域名 |

---

## 二、本地准备

确认项目可正常运行：

```powershell
# Windows 本地
cd D:\Web3\GamlaChain
python -m pytest tests/ -v      # 39 项测试应全部通过
python -m gamla_chain            # 确认能启动
```

---

## 三、服务器初始化

### 3.1 SSH 登录

```bash
ssh root@<服务器公网IP>
```

### 3.2 创建运行用户

```bash
# 创建不可登录的系统用户
sudo useradd -r -s /bin/false gamla
```

### 3.3 更新系统并安装依赖

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git nginx certbot python3-certbot-nginx
```

验证 Python 版本（需要 ≥ 3.10）：

```bash
python3 --version
```

---

## 四、部署应用

### 4.1 拉取代码

```bash
# 创建应用目录
sudo mkdir -p /opt/gamlachain

# 从 Git 克隆（替换为你的仓库地址）
cd /opt
sudo git clone <你的仓库URL> gamlachain

# 或从本地 SCP 上传
# scp -r ./* root@<IP>:/opt/gamlachain/

# 设置权限
sudo chown -R gamla:gamla /opt/gamlachain
```

### 4.2 创建虚拟环境并安装

```bash
cd /opt/gamlachain
python3 -m venv venv
venv/bin/pip install --upgrade pip
venv/bin/pip install -r requirements.txt
```

### 4.3 验证安装

```bash
venv/bin/python -c "from gamla_chain.api.server import create_app; print('OK')"
# 输出: OK
```

### 4.4 创建数据目录

```bash
sudo mkdir -p /opt/gamlachain/data
sudo chown gamla:gamla /opt/gamlachain/data
```

---

## 五、配置 Systemd 守护进程

```bash
sudo cp /opt/gamlachain/deploy/gamlachain.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable gamlachain
sudo systemctl start gamlachain
```

验证：

```bash
sudo systemctl status gamlachain
# 应显示: active (running)

curl http://localhost:8000/api/v1/chain/info
# 应返回: {"ok":true,"data":{"height":1,...}}
```

常用命令：

```bash
sudo systemctl restart gamlachain   # 重启
sudo systemctl stop gamlachain      # 停止
sudo journalctl -u gamlachain -f    # 实时日志
sudo journalctl -u gamlachain -n 50 # 最近 50 行
```

---

## 六、配置防火墙 (UFW)

```bash
# 重置防火墙
sudo ufw --force reset

# 默认拒绝所有入站
sudo ufw default deny incoming
sudo ufw default allow outgoing

# 开放必要端口
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP (Nginx)
sudo ufw allow 443/tcp   # HTTPS (Nginx)

# 激活
sudo ufw enable

# 确认
sudo ufw status verbose
```

最终端口状态：

| 端口 | 协议 | 用途 |
|------|------|------|
| 22 | TCP | SSH 远程管理 |
| 80 | TCP | HTTP（Nginx，自动跳转 HTTPS） |
| 443 | TCP | HTTPS（Nginx 终结 TLS） |
| ~~8000~~ | ~~TCP~~ | **已关闭**，仅本机 `127.0.0.1:8000` 监听 |

> ⚠️ **关键：8000 端口不对外开放**。GamlaChain 只监听 `127.0.0.1:8000`（systemd 中 `HOST=0.0.0.0` 改为 `HOST=127.0.0.1`），所有外部请求由 Nginx 反向代理。

修正 systemd 监听地址：

```bash
sudo sed -i 's/Environment=HOST=0.0.0.0/Environment=HOST=127.0.0.1/' /etc/systemd/system/gamlachain.service
sudo systemctl daemon-reload
sudo systemctl restart gamlachain
```

---

## 七、配置 Nginx 反向代理

### 7.1 创建站点配置

```bash
sudo nano /etc/nginx/sites-available/gamlachain
```

写入以下配置（将 `your-domain.com` 替换为实际域名）：

```nginx
# HTTP → HTTPS 重定向
server {
    listen 80;
    server_name your-domain.com;

    # 允许请求体最大 10MB
    client_max_body_size 10m;

    location / {
        return 301 https://$host$request_uri;
    }
}

# HTTPS 主站点
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL 证书（certbot 会自动填充）
    ssl_certificate     /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # 现代 SSL 配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;

    # 安全头
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options SAMEORIGIN;
    add_header X-XSS-Protection "1; mode=block";

    # 请求体大小限制
    client_max_body_size 10m;

    # 反向代理到 GamlaChain
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
        proxy_connect_timeout 10s;
    }
}
```

> 如果是**纯 IP 部署**（无域名），将 `server_name your-domain.com;` 改为 `server_name _;` 并删除 `return 301 https://...` 和整个 SSL server 块，仅保留 HTTP server 块。但**不推荐**纯 HTTP。

### 7.2 先以 HTTP 模式启动（等证书签发后再切 HTTPS）

如果还没有 SSL 证书，先用简化配置：

```bash
sudo nano /etc/nginx/sites-available/gamlachain
```

```nginx
server {
    listen 80;
    server_name your-domain.com;
    client_max_body_size 10m;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }
}
```

启用并测试：

```bash
sudo ln -s /etc/nginx/sites-available/gamlachain /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default    # 删掉默认站点
sudo nginx -t                                   # 测试配置语法
sudo systemctl reload nginx                     # 重载
```

现在浏览器访问 `http://<IP或域名>` 应该能看到 GamlaChain 页面了。

---

## 八、配置 HTTPS（Let's Encrypt 免费证书）

### 8.1 确保域名 DNS 已解析到服务器 IP

```bash
# 验证 DNS
dig your-domain.com +short
# 应显示你的服务器 IP
```

### 8.2 签发证书

```bash
sudo certbot --nginx -d your-domain.com
```

按提示操作：
1. 输入邮箱（用于证书到期提醒）
2. 同意服务条款
3. 选择是否接收推广邮件（N）
4. 选择 `2: Redirect`（自动将 HTTP 重定向到 HTTPS）

### 8.3 验证自动续期

```bash
# 测试续期（不会真正续期）
sudo certbot renew --dry-run

# certbot 已自动添加 systemd timer，每 12 小时检查一次
sudo systemctl status certbot.timer
```

### 8.4 最终 Nginx 配置（certbot 自动生成）

Certbot 会自动将之前的 HTTP 配置更新为完整 HTTPS 配置，包括 SSL 证书路径和安全头。可以用以下命令查看：

```bash
sudo cat /etc/nginx/sites-available/gamlachain
```

---

## 九、加固 SSH

### 9.1 生成 SSH 密钥对（在本地执行）

```powershell
# Windows PowerShell
ssh-keygen -t ed25519 -C "your-email@example.com"
# 回车使用默认路径: C:\Users\<你>\.ssh\id_ed25519
```

### 9.2 上传公钥到服务器

```powershell
# Windows 终端
type $env:USERPROFILE\.ssh\id_ed25519.pub | ssh root@<服务器IP> "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```

### 9.3 禁用密码登录

```bash
# 先测试密钥登录是否可以（开新窗口尝试）
ssh root@<服务器IP>

# 确认密钥登录正常后：
sudo nano /etc/ssh/sshd_config
```

修改以下行：

```
PermitRootLogin prohibit-password
PasswordAuthentication no
PubkeyAuthentication yes
```

重启 SSH：

```bash
sudo systemctl reload sshd
```

> ⚠️ 保持当前窗口不要关闭！开新窗口验证密钥登录正常后，再关旧窗口。

---

## 十、安装 fail2ban（防爆破）

```bash
sudo apt install -y fail2ban

# 创建本地配置
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local

# 启动
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# 查看状态
sudo fail2ban-client status
sudo fail2ban-client status sshd
```

默认配置即可生效：SSH 5 次失败后封禁 IP 10 分钟。

---

## 十一、最终验证

```bash
# 1. 检查服务状态
sudo systemctl status gamlachain nginx fail2ban

# 2. 检查监听端口（8000 应该只在 127.0.0.1）
sudo ss -tlnp | grep -E '8000|80|443'
# 应显示:
# 127.0.0.1:8000  → gamla_chain (仅本机)
# 0.0.0.0:80     → nginx
# 0.0.0.0:443    → nginx

# 3. 检查防火墙
sudo ufw status verbose

# 4. 测试 HTTPS
curl -s https://your-domain.com/api/v1/chain/info | python3 -m json.tool

# 5. SSL 评级检查（可选）
# 浏览器打开: https://www.ssllabs.com/ssltest/analyze.html?d=your-domain.com
```

---

## 十二、首次使用

1. 浏览器打开 `https://your-domain.com`
2. 点击「注册」，**第一个注册的用户自动成为管理员**
3. 管理员可访问 `/admin.html` 查看区块链、用户列表、手动挖矿
4. 用户在「水龙头」页面可领取 3 次 × 10 GLC 测试币

---

## 十三、日常维护命令速查

```bash
# 查看应用日志
sudo journalctl -u gamlachain -n 100 -f

# 查看 Nginx 访问日志
sudo tail -f /var/log/nginx/access.log

# 查看 Nginx 错误日志
sudo tail -f /var/log/nginx/error.log

# 查看 fail2ban 封禁列表
sudo fail2ban-client status sshd

# 手动解封 IP
sudo fail2ban-client set sshd unbanip <IP地址>

# 备份数据
sudo cp -r /opt/gamlachain/data /backup/gamlachain-$(date +%Y%m%d)

# 更新应用
cd /opt/gamlachain
sudo -u gamla git pull
sudo systemctl restart gamlachain

# 系统更新
sudo apt update && sudo apt upgrade -y
sudo snap refresh                        # certbot 更新
```

---

## 环境变量参考

在 `/etc/systemd/system/gamlachain.service` 中修改：

| 变量 | 生产环境值 | 说明 |
|------|-----------|------|
| `HOST` | `127.0.0.1` | 仅本机监听（Nginx 代理） |
| `PORT` | `8000` | 监听端口 |
| `MINING_DIFFICULTY` | `4` | PoW 难度 |
| `MINING_REWARD` | `50.0` | 出块奖励 (GLC) |
| `SECRET_KEY` | 随机字符串 | 安全密钥，空则自动生成 |
| `CORS_ORIGINS` | `https://your-domain.com` | 限制跨域来源 |
| `DATA_DIR` | `data` | 数据存储目录 |
