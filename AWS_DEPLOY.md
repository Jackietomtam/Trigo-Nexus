# AWS EC2 部署指南 - Trigo Nexus AI Trading Platform

## 前置要求
- AWS 账号
- EC2 实例（推荐：Ubuntu 22.04 LTS，t3.medium 或更高）
- 安全组配置：开放 80、443、5001 端口
- 域名（可选，用于 HTTPS）

## 一、准备 EC2 实例

### 1. 启动 EC2 实例
```bash
# 选择 Ubuntu 22.04 LTS
# 实例类型：t3.medium（2vCPU, 4GB RAM）或更高
# 存储：30GB gp3
```

### 2. 配置安全组
```
入站规则：
- SSH (22) - 你的 IP
- HTTP (80) - 0.0.0.0/0
- HTTPS (443) - 0.0.0.0/0
- Custom TCP (5001) - 0.0.0.0/0 [仅用于测试]
```

### 3. SSH 登录
```bash
ssh -i your-key.pem ubuntu@<EC2_PUBLIC_IP>
```

## 二、安装系统依赖

```bash
# 更新系统
sudo apt update && sudo apt -y upgrade

# 安装必要软件
sudo apt install -y \
    build-essential \
    python3.10 \
    python3.10-venv \
    python3-pip \
    nginx \
    git \
    supervisor \
    certbot \
    python3-certbot-nginx
```

## 三、部署应用

### 1. 克隆代码
```bash
cd /opt
sudo git clone https://github.com/YOUR_USERNAME/AI-Trading.git ai-trader
sudo chown -R ubuntu:ubuntu ai-trader
cd ai-trader
```

### 2. 创建虚拟环境
```bash
python3.10 -m venv venv
source venv/bin/activate
pip install --upgrade pip wheel setuptools
pip install -r requirements.txt
```

### 3. 配置环境变量
```bash
# 创建 .env 文件
cat > /opt/ai-trader/.env << 'EOF'
HOST=0.0.0.0
PORT=5001
FINNHUB_API_KEY=你的Finnhub_API_KEY
DASHSCOPE_API_KEY=你的阿里云QWEN_API_KEY
DASHSCOPE_DEEPSEEK_API_KEY=你的阿里云DeepSeek_API_KEY
EOF

# 设置文件权限
chmod 600 /opt/ai-trader/.env
```

### 4. 测试运行
```bash
source venv/bin/activate
cd /opt/ai-trader
export $(cat .env | xargs)
gunicorn -k eventlet -w 1 app_dual_edition:app --bind 0.0.0.0:5001
```

访问 `http://<EC2_PUBLIC_IP>:5001/edition2` 验证是否正常运行。
验证成功后按 `Ctrl+C` 停止。

## 四、配置 Systemd 服务

### 1. 创建服务文件
```bash
sudo tee /etc/systemd/system/ai-trader.service << 'EOF'
[Unit]
Description=Trigo Nexus AI Trading Platform
After=network.target

[Service]
Type=notify
User=ubuntu
Group=ubuntu
WorkingDirectory=/opt/ai-trader
EnvironmentFile=/opt/ai-trader/.env
ExecStart=/opt/ai-trader/venv/bin/gunicorn \
    -k eventlet \
    -w 1 \
    --bind 0.0.0.0:5001 \
    --timeout 120 \
    --access-logfile /var/log/ai-trader/access.log \
    --error-logfile /var/log/ai-trader/error.log \
    app_dual_edition:app
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=ai-trader

[Install]
WantedBy=multi-user.target
EOF
```

### 2. 创建日志目录
```bash
sudo mkdir -p /var/log/ai-trader
sudo chown ubuntu:ubuntu /var/log/ai-trader
```

### 3. 启动服务
```bash
sudo systemctl daemon-reload
sudo systemctl enable ai-trader
sudo systemctl start ai-trader
sudo systemctl status ai-trader
```

### 4. 查看日志
```bash
# 实时日志
sudo journalctl -u ai-trader -f

# 应用日志
tail -f /var/log/ai-trader/error.log
tail -f /var/log/ai-trader/access.log
```

## 五、配置 Nginx 反向代理

### 1. 创建 Nginx 配置
```bash
sudo tee /etc/nginx/sites-available/ai-trader << 'EOF'
upstream ai_trader {
    server 127.0.0.1:5001;
}

server {
    listen 80;
    server_name _;  # 替换为你的域名

    client_max_body_size 10M;

    # 访问日志
    access_log /var/log/nginx/ai-trader-access.log;
    error_log /var/log/nginx/ai-trader-error.log;

    # 静态文件
    location /static/ {
        alias /opt/ai-trader/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # WebSocket 和 HTTP 请求
    location / {
        proxy_pass http://ai_trader;
        proxy_http_version 1.1;
        
        # WebSocket 支持
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 标准代理头
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
        send_timeout 600s;
    }
}
EOF
```

### 2. 启用配置
```bash
# 测试配置
sudo nginx -t

# 启用站点
sudo ln -sf /etc/nginx/sites-available/ai-trader /etc/nginx/sites-enabled/ai-trader

# 删除默认站点（可选）
sudo rm -f /etc/nginx/sites-enabled/default

# 重启 Nginx
sudo systemctl restart nginx
```

### 3. 验证
访问 `http://<EC2_PUBLIC_IP>/edition2` 应该能看到应用。

## 六、配置 HTTPS（可选但推荐）

### 1. 使用 Let's Encrypt 免费证书
```bash
# 确保已将域名解析到 EC2 公网 IP
# 将下面的 your-domain.com 替换为你的实际域名

sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

### 2. 自动续期
```bash
# Certbot 会自动配置续期，测试一下
sudo certbot renew --dry-run
```

## 七、性能优化（可选）

### 1. 配置 Supervisor（替代 systemd，更方便管理）
```bash
sudo tee /etc/supervisor/conf.d/ai-trader.conf << 'EOF'
[program:ai-trader]
command=/opt/ai-trader/venv/bin/gunicorn -k eventlet -w 1 --bind 0.0.0.0:5001 app_dual_edition:app
directory=/opt/ai-trader
user=ubuntu
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/ai-trader/supervisor.log
environment=HOST="0.0.0.0",PORT="5001",FINNHUB_API_KEY="xxx",DASHSCOPE_API_KEY="xxx",DASHSCOPE_DEEPSEEK_API_KEY="xxx"
EOF

sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl status ai-trader
```

### 2. 配置 Swap（如果内存不足）
```bash
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

## 八、监控和维护

### 1. 查看服务状态
```bash
# Systemd 方式
sudo systemctl status ai-trader

# Supervisor 方式
sudo supervisorctl status ai-trader
```

### 2. 重启服务
```bash
# Systemd
sudo systemctl restart ai-trader

# Supervisor
sudo supervisorctl restart ai-trader
```

### 3. 查看实时日志
```bash
# 应用日志
sudo journalctl -u ai-trader -f

# Nginx 日志
sudo tail -f /var/log/nginx/ai-trader-access.log
sudo tail -f /var/log/nginx/ai-trader-error.log
```

### 4. 更新代码
```bash
cd /opt/ai-trader
sudo -u ubuntu git pull
sudo -u ubuntu /opt/ai-trader/venv/bin/pip install -r requirements.txt
sudo systemctl restart ai-trader
# 或
sudo supervisorctl restart ai-trader
```

## 九、常见问题排查

### 1. 服务无法启动
```bash
# 查看详细错误
sudo journalctl -u ai-trader -n 100 --no-pager

# 检查端口占用
sudo netstat -tulpn | grep 5001

# 手动测试启动
cd /opt/ai-trader
source venv/bin/activate
export $(cat .env | xargs)
python app_dual_edition.py
```

### 2. WebSocket 连接失败
- 确认 Nginx 配置了 `Upgrade` 和 `Connection` 头
- 确认使用了 `eventlet` worker
- 检查防火墙和安全组设置

### 3. API 调用失败
- 确认 `.env` 文件中的 API Key 正确
- 检查网络连接：`ping api.finnhub.io`
- 查看错误日志定位具体 API

### 4. 内存不足
```bash
# 查看内存使用
free -h
htop

# 考虑升级实例或增加 swap
```

## 十、安全建议

1. **限制 SSH 访问**：仅允许特定 IP 访问 22 端口
2. **关闭调试端口**：生产环境删除 5001 端口的入站规则
3. **定期更新**：
   ```bash
   sudo apt update && sudo apt upgrade
   ```
4. **备份数据**：定期备份 `/opt/ai-trader` 目录
5. **使用 IAM 角色**：如果需要访问其他 AWS 服务，使用 IAM 角色而非硬编码密钥

## 快速部署脚本（一键部署）

将以下内容保存为 `deploy.sh` 并执行：

```bash
#!/bin/bash
set -e

echo "🚀 Starting AI Trader deployment..."

# 安装依赖
sudo apt update
sudo apt install -y build-essential python3.10 python3.10-venv python3-pip nginx git

# 克隆代码
cd /opt
sudo git clone YOUR_REPO_URL ai-trader
sudo chown -R ubuntu:ubuntu ai-trader
cd ai-trader

# 创建虚拟环境
python3.10 -m venv venv
source venv/bin/activate
pip install --upgrade pip wheel
pip install -r requirements.txt

# 配置环境变量（需要手动填写 API Keys）
echo "⚠️  请编辑 /opt/ai-trader/.env 填入你的 API Keys"
cat > .env << 'EOF'
HOST=0.0.0.0
PORT=5001
FINNHUB_API_KEY=YOUR_KEY_HERE
DASHSCOPE_API_KEY=YOUR_KEY_HERE
DASHSCOPE_DEEPSEEK_API_KEY=YOUR_KEY_HERE
EOF

# 创建日志目录
sudo mkdir -p /var/log/ai-trader
sudo chown ubuntu:ubuntu /var/log/ai-trader

# 配置 systemd 服务
sudo tee /etc/systemd/system/ai-trader.service << 'EOF'
[Unit]
Description=Trigo Nexus AI Trading Platform
After=network.target

[Service]
Type=notify
User=ubuntu
WorkingDirectory=/opt/ai-trader
EnvironmentFile=/opt/ai-trader/.env
ExecStart=/opt/ai-trader/venv/bin/gunicorn -k eventlet -w 1 --bind 0.0.0.0:5001 app_dual_edition:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable ai-trader

# 配置 Nginx
sudo tee /etc/nginx/sites-available/ai-trader << 'EOF'
server {
    listen 80;
    server_name _;
    
    location /static/ {
        alias /opt/ai-trader/static/;
    }
    
    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 600s;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/ai-trader /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

echo "✅ Deployment complete!"
echo "📝 Next steps:"
echo "1. Edit /opt/ai-trader/.env with your API keys"
echo "2. Start service: sudo systemctl start ai-trader"
echo "3. Check status: sudo systemctl status ai-trader"
echo "4. View logs: sudo journalctl -u ai-trader -f"
```

## 访问地址

- Edition 1: `http://your-domain.com/edition1`
- Edition 2: `http://your-domain.com/edition2`
- Models: `http://your-domain.com/models`

---

**部署完成后，记得在浏览器访问并验证所有功能正常运行！**





