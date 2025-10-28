#!/bin/bash
set -e

EC2_IP="3.106.191.40"
EC2_USER="ubuntu"
KEY_FILE="$HOME/Downloads/trigo-key.pem"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🚀 Quick Deploy to AWS${NC}"
echo ""

# 设置密钥权限
chmod 400 "$KEY_FILE"

# 1. 在 EC2 上执行完整部署
echo -e "${YELLOW}📦 Deploying via SSH...${NC}"
ssh -i "$KEY_FILE" "$EC2_USER@$EC2_IP" << 'ENDSSH'
set -e

# 安装依赖
echo "📦 Installing dependencies..."
sudo apt update -qq
sudo apt install -y build-essential python3.10 python3.10-venv python3-pip nginx git rsync > /dev/null 2>&1

# 克隆代码(如果目录存在则更新)
if [ -d "/opt/ai-trader/.git" ]; then
    echo "📥 Updating existing code..."
    cd /opt/ai-trader
    git fetch origin
    git reset --hard origin/main
    sudo chown -R ubuntu:ubuntu /opt/ai-trader
else
    echo "📥 Cloning repository..."
    echo "⚠️  需要手动上传代码或配置Git仓库"
    sudo mkdir -p /opt/ai-trader
    sudo chown -R ubuntu:ubuntu /opt/ai-trader
fi

# 创建虚拟环境
cd /opt/ai-trader
if [ ! -d "venv" ]; then
    echo "🐍 Creating virtual environment..."
    python3.10 -m venv venv
fi

# 安装Python依赖
echo "📚 Installing Python packages..."
source venv/bin/activate
pip install --upgrade pip wheel setuptools -q
pip install Flask Flask-Cors Flask-SocketIO python-socketio python-engineio requests pandas numpy gunicorn eventlet -q

# 配置环境变量
if [ ! -f ".env" ]; then
    cat > .env << 'EOF'
HOST=0.0.0.0
PORT=5001
FINNHUB_API_KEY=YOUR_KEY
DASHSCOPE_API_KEY=YOUR_KEY
DASHSCOPE_DEEPSEEK_API_KEY=YOUR_KEY
EOF
    chmod 600 .env
    echo "⚠️  Created .env template"
fi

# 创建日志目录
sudo mkdir -p /var/log/ai-trader
sudo chown ubuntu:ubuntu /var/log/ai-trader

# 配置 systemd
sudo tee /etc/systemd/system/ai-trader.service > /dev/null << 'EOF'
[Unit]
Description=Trigo Nexus AI Trading Platform
After=network.target

[Service]
Type=notify
User=ubuntu
WorkingDirectory=/opt/ai-trader
EnvironmentFile=/opt/ai-trader/.env
ExecStart=/opt/ai-trader/venv/bin/gunicorn -k eventlet -w 1 --bind 0.0.0.0:5001 --timeout 120 app_dual_edition:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 配置 Nginx
sudo tee /etc/nginx/sites-available/ai-trader > /dev/null << 'EOF'
server {
    listen 80;
    server_name _;
    
    location /static/ {
        alias /opt/ai-trader/static/;
        expires 30d;
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

sudo ln -sf /etc/nginx/sites-available/ai-trader /etc/nginx/sites-enabled/ai-trader
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx

sudo systemctl daemon-reload
sudo systemctl enable ai-trader

echo ""
echo "✅ Setup complete!"
echo ""
echo "⚠️  Next: Upload your code and configure .env"
ENDSSH

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Server configured!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next steps:"
echo ""
echo "1. Upload code:"
echo -e "   ${GREEN}rsync -avz --exclude='venv*' --exclude='*.pyc' --exclude='__pycache__' --exclude='.git' --exclude='*.log' -e 'ssh -i $KEY_FILE' . $EC2_USER@$EC2_IP:/opt/ai-trader/${NC}"
echo ""
echo "2. Configure API keys:"
echo -e "   ${GREEN}ssh -i $KEY_FILE $EC2_USER@$EC2_IP${NC}"
echo -e "   ${GREEN}nano /opt/ai-trader/.env${NC}"
echo ""
echo "3. Start service:"
echo -e "   ${GREEN}ssh -i $KEY_FILE $EC2_USER@$EC2_IP 'sudo systemctl start ai-trader'${NC}"
echo ""



