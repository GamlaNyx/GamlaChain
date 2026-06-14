# GamlaChain 部署指南

## 服务器部署步骤

### 1. 准备环境
```bash
sudo apt update && sudo apt install -y python3 python3-pip
```

### 2. 上传代码
```bash
scp -r GamlaChain/ user@server:/opt/gamlachain/
```

### 3. 安装依赖
```bash
cd /opt/gamlachain
pip install -r requirements.txt
```

### 4. 创建管理员账户
首次启动后，第一个在网页上注册的用户将自动成为 **管理员**。
管理员可以访问 `/admin.html` 控制台查看区块链状态、用户列表、手动挖矿。

### 5. 配置 systemd 守护进程
```bash
sudo cp deploy/gamlachain.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable gamlachain
sudo systemctl start gamlachain
```

### 6. 检查运行状态
```bash
sudo systemctl status gamlachain
curl http://localhost:8000/api/v1/chain/info
```

### 7. 打开浏览器
```
http://<服务器IP>:8000/
```

---

## 可选：配置 Nginx 反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

配置 HTTPS（推荐生产环境）：
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| HOST | 127.0.0.1 | API 监听地址 (部署时设为 0.0.0.0) |
| PORT | 8000 | API 端口 |
| MINING_DIFFICULTY | 4 | PoW 难度 (前导零个数) |
| MINING_REWARD | 50.0 | 出块奖励 (GLC) |
| DATA_DIR | data | 数据持久化目录 |
| STATIC_DIR | frontend | 前端静态文件目录 |
