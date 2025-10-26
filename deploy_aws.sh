#!/bin/bash
# AWS EC2 一键部署脚本 - Trigo Nexus AI Trading System
# 适用于 Ubuntu 22.04 LTS (推荐) 或 Amazon Linux 2023

set -e  # 遇到错误立即退出

echo "🚀 Trigo Nexus AWS 部署脚本"
echo "=============================="
echo ""

# 1. 更新系统
echo "📦 步骤 1/8: 更新系统包..."
sudo apt-get update -y || sudo yum update -y
sudo apt-get upgrade -y || sudo yum upgrade -y

# 2. 安装 Python 3.10 和 pip
echo "🐍 步骤 2/8: 安装 Python 3.10..."
if command -v apt-get &> /dev/null; then
    # Ubuntu/Debian
    sudo apt-get install -y python3.10 python3.10-venv python3-pip git
elif command -v yum &> /dev/null; then
    # Amazon Linux
    sudo yum install -y python3.10 python3-pip git
fi

# 3. 克隆代码（或上传代码）
echo "📥 步骤 3/8: 获取代码..."
cd ~
if [ -d "Trigo-Nexus" ]; then
    echo "⚠️  代码目录已存在，拉取最新代码..."
    cd Trigo-Nexus
    git pull
else
    echo "📥 克隆 GitHub 仓库..."
    git clone https://github.com/Jackietomtam/Trigo-Nexus.git
    cd Trigo-Nexus
fi

# 4. 创建虚拟环境
echo "🔧 步骤 4/8: 创建 Python 虚拟环境..."
python3.10 -m venv venv
source venv/bin/activate

# 5. 安装依赖
echo "📦 步骤 5/8: 安装 Python 依赖..."
pip install --upgrade pip
pip install -r requirements.txt

# 6. 配置环境变量
echo "🔑 步骤 6/8: 配置环境变量..."
cat > .env << 'EOF'
# API Keys
OPENROUTER_API_KEY=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
DASHSCOPE_API_KEY=sk-79529efd5f434d8aa9eea08c17441096
FINNHUB_API_KEY=d1ivl31r01qhbuvsiufgd1ivl31r01qhbuvsiug0

# Flask 配置
FLASK_ENV=production
PORT=5001
EOF

# 7. 创建 systemd 服务（自动启动）
echo "⚙️  步骤 7/8: 配置自动启动服务..."
sudo tee /etc/systemd/system/trigo-nexus.service > /dev/null << EOF
[Unit]
Description=Trigo Nexus AI Trading System
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$HOME/Trigo-Nexus
Environment="PATH=$HOME/Trigo-Nexus/venv/bin"
EnvironmentFile=$HOME/Trigo-Nexus/.env
ExecStart=$HOME/Trigo-Nexus/venv/bin/python app_v2.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 8. 启动服务
echo "🚀 步骤 8/8: 启动服务..."
sudo systemctl daemon-reload
sudo systemctl enable trigo-nexus
sudo systemctl start trigo-nexus

# 9. 配置防火墙
echo "🔥 配置防火墙规则..."
if command -v ufw &> /dev/null; then
    sudo ufw allow 5001/tcp
    sudo ufw allow 22/tcp  # SSH
    sudo ufw --force enable
fi

# 10. 显示状态
echo ""
echo "✅ 部署完成！"
echo "=============================="
echo ""
echo "📊 服务状态:"
sudo systemctl status trigo-nexus --no-pager
echo ""
echo "📋 查看日志:"
echo "  sudo journalctl -u trigo-nexus -f"
echo ""
echo "🌐 访问地址:"
echo "  http://$(curl -s ifconfig.me):5001/"
echo ""
echo "🔄 管理命令:"
echo "  启动: sudo systemctl start trigo-nexus"
echo "  停止: sudo systemctl stop trigo-nexus"
echo "  重启: sudo systemctl restart trigo-nexus"
echo "  状态: sudo systemctl status trigo-nexus"
echo "  日志: sudo journalctl -u trigo-nexus -f"
echo ""
echo "🎉 享受你的 AI 交易系统！"

