#!/bin/bash
set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Trigo Nexus AI Trading Platform - AWS Deployment Script${NC}"
echo ""

# 检查是否为 root
if [ "$EUID" -eq 0 ]; then 
    echo -e "${RED}❌ Please do not run as root. Run as ubuntu user.${NC}"
    exit 1
fi

# 1. 更新系统
echo -e "${YELLOW}📦 Step 1/8: Updating system packages...${NC}"
sudo apt update
sudo apt upgrade -y

# 2. 安装依赖
echo -e "${YELLOW}📦 Step 2/8: Installing dependencies...${NC}"
sudo apt install -y \
    build-essential \
    python3.10 \
    python3.10-venv \
    python3-pip \
    nginx \
    git \
    certbot \
    python3-certbot-nginx

# 3. 克隆或更新代码
echo -e "${YELLOW}📦 Step 3/8: Setting up application code...${NC}"
if [ -d "/opt/ai-trader" ]; then
    echo "Directory exists, pulling latest changes..."
    cd /opt/ai-trader
    git pull
else
    echo "Cloning repository..."
    cd /opt
    # 如果是本地部署，从当前目录复制
    if [ -f "$(pwd)/app_dual_edition.py" ]; then
        sudo mkdir -p /opt/ai-trader
        sudo cp -r . /opt/ai-trader/
    else
        echo -e "${RED}⚠️  Please clone your repository manually:${NC}"
        echo "sudo git clone YOUR_REPO_URL /opt/ai-trader"
        exit 1
    fi
fi

sudo chown -R $USER:$USER /opt/ai-trader

# 4. 创建虚拟环境
echo -e "${YELLOW}📦 Step 4/8: Creating Python virtual environment...${NC}"
cd /opt/ai-trader
python3.10 -m venv venv
source venv/bin/activate
pip install --upgrade pip wheel setuptools
pip install -r requirements.txt

# 5. 配置环境变量
echo -e "${YELLOW}📦 Step 5/8: Configuring environment variables...${NC}"
if [ ! -f "/opt/ai-trader/.env" ]; then
    cat > /opt/ai-trader/.env << 'EOF'
HOST=0.0.0.0
PORT=5001
FINNHUB_API_KEY=YOUR_FINNHUB_KEY_HERE
DASHSCOPE_API_KEY=YOUR_QWEN_KEY_HERE
DASHSCOPE_DEEPSEEK_API_KEY=YOUR_DEEPSEEK_KEY_HERE
EOF
    chmod 600 /opt/ai-trader/.env
    echo -e "${YELLOW}⚠️  Created .env file. Please edit it with your API keys:${NC}"
    echo "nano /opt/ai-trader/.env"
else
    echo "✅ .env file already exists"
fi

# 6. 创建日志目录
echo -e "${YELLOW}📦 Step 6/8: Creating log directories...${NC}"
sudo mkdir -p /var/log/ai-trader
sudo chown $USER:$USER /var/log/ai-trader

# 7. 配置 Systemd 服务
echo -e "${YELLOW}📦 Step 7/8: Configuring systemd service...${NC}"
sudo tee /etc/systemd/system/ai-trader.service > /dev/null << 'EOF'
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

sudo systemctl daemon-reload
sudo systemctl enable ai-trader

# 8. 配置 Nginx
echo -e "${YELLOW}📦 Step 8/8: Configuring Nginx...${NC}"
sudo tee /etc/nginx/sites-available/ai-trader > /dev/null << 'EOF'
upstream ai_trader {
    server 127.0.0.1:5001;
}

server {
    listen 80;
    server_name _;

    client_max_body_size 10M;

    access_log /var/log/nginx/ai-trader-access.log;
    error_log /var/log/nginx/ai-trader-error.log;

    location /static/ {
        alias /opt/ai-trader/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location / {
        proxy_pass http://ai_trader;
        proxy_http_version 1.1;
        
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
        send_timeout 600s;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/ai-trader /etc/nginx/sites-enabled/ai-trader
sudo rm -f /etc/nginx/sites-enabled/default

# 测试 Nginx 配置
if sudo nginx -t; then
    sudo systemctl restart nginx
    echo -e "${GREEN}✅ Nginx configured successfully${NC}"
else
    echo -e "${RED}❌ Nginx configuration test failed${NC}"
    exit 1
fi

# 完成
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}📝 Next steps:${NC}"
echo ""
echo "1. Edit environment variables with your API keys:"
echo "   nano /opt/ai-trader/.env"
echo ""
echo "2. Start the service:"
echo "   sudo systemctl start ai-trader"
echo ""
echo "3. Check service status:"
echo "   sudo systemctl status ai-trader"
echo ""
echo "4. View logs:"
echo "   sudo journalctl -u ai-trader -f"
echo ""
echo "5. Access your application:"
echo "   http://$(curl -s ifconfig.me)/edition2"
echo ""
echo -e "${YELLOW}Optional: Enable HTTPS${NC}"
echo "   sudo certbot --nginx -d your-domain.com"
echo ""





