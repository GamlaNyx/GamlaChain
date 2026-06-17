# GamlaChain 服务器部署指南

## 一、服务器要求

| 项目 | 最低配置 |
|------|---------|
| 系统 | Ubuntu 20.04+ / Debian 11+ / CentOS 8+ |
| CPU | 1 核（PoW 难度4时足够） |
| 内存 | 512 MB |
| 磁盘 | 2 GB（链数据很小，JSON 文件存储） |
| 网络 | 公网 IP，开放 8000 端口（或通过 Nginx 80/443） |
| Python | 3.10+ |

**推荐：** 阿里云 / 腾讯云轻量应用服务器，1核1G 最低配即可，约 50-70 元/月。

---

## 二、本地准备

部署前确保本地项目可正常运行：

```bash
# Windows 本地验证
cd D:\Web3\GamlaChain
python -m pytest tests/ -v     # 39 个测试应全部通过
python -m gamla_chain           # 确认能启动
```

---

## 三、服务器环境配置

### 3.1 SSH 登录

```bash
ssh root@<服务器公网IP>
```

### 3.2 安装 Python 和依赖

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git

# 验证版本（需要 3.10+）
python3 --version
```

### 3.3 创建目录和用户

```bash
# 创建应用目录
sudo mkdir -p /opt/gamlachain

# 创建运行用户（不要用 root 运行）
sudo useradd -r -s /bin/false gamla 2>/dev/null || true

# 设置权限
sudo chown -R gamla:gamla /opt/gamlachain
```

---

## 四、上传代码

### 方式一：SCP 上传（从本地直接传）

在本地 Windows 终端执行：

```bash
# 先排除不需要的文件
cd D:\Web3\GamlaChain
# 然后上传（在 Git Bash 或 WSL 中执行）
scp -r ./* root@<服务器IP>:/opt/gamlachain/
```

### 方式二：Git 克隆（推荐）

在服务器上执行：

```bash
# 如果代码已推送到 GitHub/Gitee
cd /opt
sudo git clone <你的仓库地址> gamlachain
sudo chown -R gamla:gamla /opt/gamlachain
```

---

## 五、安装项目

```bash
cd /opt/gamlachain

# 创建虚拟环境
python3 -m venv venv

# 安装依赖
venv/bin/pip install -r requirements.txt

# 验证安装
venv/bin/python -c "from gamla_chain.api.server import create_app; print('OK')"
```

---

## 六、配置 Systemd

```bash
# 复制服务文件
sudo cp deploy/gamlachain.service /etc/systemd/system/

# 重载并启动
sudo systemctl daemon-reload
sudo systemctl enable gamlachain
sudo systemctl start gamlachain

# 查看状态
sudo systemctl status gamlachain

# 查看日志
sudo journalctl -u gamlachain -f
```

---

## 七、配置防火墙

```bash
# Ubuntu/Debian (ufw)
sudo ufw allow 22/tcp        # SSH
sudo ufw allow 8000/tcp      # GamlaChain
sudo ufw enable

# 阿里云/腾讯云用户还需在控制台安全组中放行 8000 端口
```

---

## 八、验证部署

```bash
# 本地测试
curl http://localhost:8000/api/v1/chain/info

# 应返回：
# {"ok":true,"data":{"height":1,"difficulty":4,...}}

# 从外网访问
# 浏览器打开: http://<服务器公网IP>:8000
```

**第一个注册的用户自动成为管理员**，可访问 `/admin.html` 管理区块链。

---

## 九、可选：Nginx 反向代理 + 域名 + HTTPS

### 9.1 安装 Nginx

```bash
sudo apt install -y nginx
```

### 9.2 配置站点

```bash
sudo nano /etc/nginx/sites-available/gamlachain
```

写入：

```nginx
server {
    listen 80;
    server_name your-domain.com;   # 改成你的域名或服务器IP

    client_max_body_size 10m;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 120s;
    }
}
```

启用站点：

```bash
sudo ln -s /etc/nginx/sites-available/gamlachain /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### 9.3 HTTPS（Let's Encrypt 免费证书）

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
# 按提示操作，选择自动重定向 HTTP → HTTPS
```

配置完 HTTPS 后关闭 8000 端口：

```bash
sudo ufw delete allow 8000/tcp
```

---

## 十、日常维护

```bash
# 查看服务状态
sudo systemctl status gamlachain

# 重启服务
sudo systemctl restart gamlachain

# 查看日志
sudo journalctl -u gamlachain -n 50

# 备份数据
sudo cp -r /opt/gamlachain/data /backup/gamlachain-$(date +%Y%m%d)

# 更新代码
cd /opt/gamlachain
sudo -u gamla git pull
sudo systemctl restart gamlachain
```

---

## 环境变量参考

可在 systemd service 文件中修改：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `HOST` | `0.0.0.0` | 监听地址 |
| `PORT` | `8000` | 监听端口 |
| `MINING_DIFFICULTY` | `4` | PoW 难度（前导零数，4 约 1-5 秒出块） |
| `MINING_REWARD` | `50.0` | 出块奖励 (GLC) |
| `DATA_DIR` | `data` | 数据存储目录 |
| `STATIC_DIR` | `frontend` | 前端文件目录 |
