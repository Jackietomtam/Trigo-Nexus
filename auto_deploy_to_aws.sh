#!/bin/bash
set -e

# AWS EC2 配置
EC2_IP="3.106.191.40"
EC2_USER="ubuntu"
KEY_FILE="$HOME/Downloads/trigo-key.pem"
REMOTE_DIR="/opt/ai-trader"
LOCAL_DIR="$(cd "$(dirname "$0")" && pwd)"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}🚀 Trigo Nexus - Auto Deploy to AWS${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Target: ${EC2_USER}@${EC2_IP}${NC}"
echo ""

# 检查密钥文件
if [ ! -f "$KEY_FILE" ]; then
    echo -e "${RED}❌ SSH key not found: $KEY_FILE${NC}"
    exit 1
fi

# 设置密钥权限
chmod 400 "$KEY_FILE"

# 测试连接
echo -e "${YELLOW}🔌 Testing SSH connection...${NC}"
if ! ssh -i "$KEY_FILE" -o ConnectTimeout=10 -o StrictHostKeyChecking=no "$EC2_USER@$EC2_IP" "echo '✓ Connected'" 2>/dev/null; then
    echo -e "${RED}❌ Cannot connect to EC2. Please check:${NC}"
    echo "   - Security group allows SSH (port 22) from your IP"
    echo "   - EC2 instance is running"
    echo "   - Key file is correct"
    exit 1
fi
echo -e "${GREEN}✅ SSH connection successful${NC}"
echo ""

# 1. 上传代码
echo -e "${YELLOW}📤 Step 1/6: Uploading code to EC2...${NC}"
ssh -i "$KEY_FILE" "$EC2_USER@$EC2_IP" "sudo rm -rf /tmp/ai-trader-upload"
scp -i "$KEY_FILE" -r "$LOCAL_DIR" "$EC2_USER@$EC2_IP:/tmp/ai-trader-upload"
echo -e "${GREEN}✅ Code uploaded${NC}"
echo ""

# 2. 安装系统依赖
echo -e "${YELLOW}📦 Step 2/6: Installing system dependencies...${NC}"
ssh -i "$KEY_FILE" "$EC2_USER@$EC2_IP" << 'ENDSSH'
set -e
echo "Updating system packages..."
sudo apt update -qq
sudo apt install -y build-essential python3.10 python3.10-venv python3-pip nginx git curl > /dev/null 2>&1
echo "✓ System dependencies installed"
ENDSSH
echo -e "${GREEN}✅ System dependencies installed${NC}"
echo ""

# 3. 设置应用目录
echo -e "${YELLOW}📁 Step 3/6: Setting up application directory...${NC}"
ssh -i "$KEY_FILE" "$EC2_USER@$EC2_IP" << 'ENDSSH'
set -e
sudo mkdir -p /opt/ai-trader
sudo rm -rf /opt/ai-trader/*
sudo mv /tmp/ai-trader-upload/* /opt/ai-trader/
sudo chown -R ubuntu:ubuntu /opt/ai-trader
echo "✓ Application directory ready"
ENDSSH
echo -e "${GREEN}✅ Application directory ready${NC}"
echo ""

# 4. 创建虚拟环境并安装依赖
echo -e "${YELLOW}🐍 Step 4/6: Setting up Python virtual environment...${NC}"
ssh -i "$KEY_FILE" "$EC2_USER@$EC2_IP" << 'ENDSSH'
set -e
cd /opt/ai-trader
python3.10 -m venv venv
source venv/bin/activate
pip install --upgrade pip wheel setuptools -q
pip install -r requirements.txt -q
echo "✓ Python environment ready"
ENDSSH
echo -e "${GREEN}✅ Python environment ready${NC}"
echo ""

# 5. 配置服务和 Nginx
echo -e "${YELLOW}⚙️  Step 5/6: Configuring systemd and Nginx...${NC}"
ssh -i "$KEY_FILE" "$EC2_USER@$EC2_IP" << 'ENDSSH'
set -e

# 创建 .env 文件（如果不存在）
if [ ! -f /opt/ai-trader/.env ]; then
    cat > /opt/ai-trader/.env << 'EOF'
HOST=0.0.0.0
PORT=5001
FINNHUB_API_KEY=YOUR_FINNHUB_KEY
DASHSCOPE_API_KEY=YOUR_QWEN_KEY
DASHSCOPE_DEEPSEEK_API_KEY=YOUR_DEEPSEEK_KEY
EOF
    chmod 600 /opt/ai-trader/.env
    echo "⚠️  Created .env template - please update with real API keys"
fi

# 创建日志目录
sudo mkdir -p /var/log/ai-trader
sudo chown ubuntu:ubuntu /var/log/ai-trader

# 配置 systemd 服务
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

# 配置 Nginx
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
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/ai-trader /etc/nginx/sites-enabled/ai-trader
sudo rm -f /etc/nginx/sites-enabled/default

# 测试并重启 Nginx
if sudo nginx -t > /dev/null 2>&1; then
    sudo systemctl restart nginx
    echo "✓ Nginx configured and restarted"
else
    echo "✗ Nginx configuration error"
    exit 1
fi

# 重载 systemd
sudo systemctl daemon-reload
sudo systemctl enable ai-trader

echo "✓ Services configured"
ENDSSH
echo -e "${GREEN}✅ Services configured${NC}"
echo ""

# 6. 提示配置 API Keys
echo -e "${YELLOW}🔑 Step 6/6: API Keys Configuration${NC}"
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}⚠️  IMPORTANT: You need to configure your API keys${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Please edit the .env file on the server:"
echo ""
echo -e "${GREEN}ssh -i $KEY_FILE $EC2_USER@$EC2_IP${NC}"
echo -e "${GREEN}nano /opt/ai-trader/.env${NC}"
echo ""
echo "Fill in your API keys:"
echo "  - FINNHUB_API_KEY (get from https://finnhub.io)"
echo "  - DASHSCOPE_API_KEY (get from https://dashscope.aliyun.com)"
echo "  - DASHSCOPE_DEEPSEEK_API_KEY (same as above)"
echo ""
read -p "Press Enter after you've configured the API keys..."

# 7. 启动服务
echo ""
echo -e "${YELLOW}🚀 Starting the application...${NC}"
ssh -i "$KEY_FILE" "$EC2_USER@$EC2_IP" << 'ENDSSH'
sudo systemctl start ai-trader
sleep 3
if sudo systemctl is-active --quiet ai-trader; then
    echo "✓ Application started successfully"
else
    echo "✗ Application failed to start"
    echo "Check logs: sudo journalctl -u ai-trader -n 50"
    exit 1
fi
ENDSSH

# 完成
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}📍 Access your application:${NC}"
echo ""
echo -e "   Edition 1: ${GREEN}http://${EC2_IP}/edition1${NC}"
echo -e "   Edition 2: ${GREEN}http://${EC2_IP}/edition2${NC}"
echo -e "   Models:    ${GREEN}http://${EC2_IP}/models${NC}"
echo ""
echo -e "${BLUE}📊 Useful commands:${NC}"
echo ""
echo "   Check status:"
echo -e "   ${GREEN}ssh -i $KEY_FILE $EC2_USER@$EC2_IP 'sudo systemctl status ai-trader'${NC}"
echo ""
echo "   View logs:"
echo -e "   ${GREEN}ssh -i $KEY_FILE $EC2_USER@$EC2_IP 'sudo journalctl -u ai-trader -f'${NC}"
echo ""
echo "   Restart service:"
echo -e "   ${GREEN}ssh -i $KEY_FILE $EC2_USER@$EC2_IP 'sudo systemctl restart ai-trader'${NC}"
echo ""
echo -e "${YELLOW}⚠️  Remember to configure security group to allow HTTP (port 80)${NC}"
echo ""



