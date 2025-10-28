#!/bin/bash
set -e

EC2_IP="3.106.191.40"
EC2_USER="ubuntu"
KEY_FILE="$HOME/Downloads/trigo-key.pem"
LOCAL_DIR="$(cd "$(dirname "$0")" && pwd)"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🚀 部署到 AWS (tar 方式)${NC}"
echo ""

chmod 400 "$KEY_FILE"

# 1. 本地打包（排除不必要的文件）
echo -e "${YELLOW}📦 打包代码...${NC}"
cd "$LOCAL_DIR"
tar --exclude='venv*' --exclude='__pycache__' --exclude='*.pyc' \
    --exclude='.git' --exclude='*.log' --exclude='.env' \
    -czf /tmp/ai-trader-deploy.tgz .
echo -e "${GREEN}✅ 打包完成${NC}"
echo ""

# 2. 上传
echo -e "${YELLOW}📤 上传到服务器...${NC}"
scp -i "$KEY_FILE" /tmp/ai-trader-deploy.tgz "$EC2_USER@$EC2_IP:/tmp/"
echo -e "${GREEN}✅ 上传完成${NC}"
echo ""

# 3. 服务器端解压并重启
echo -e "${YELLOW}⚙️  部署并重启...${NC}"
ssh -i "$KEY_FILE" "$EC2_USER@$EC2_IP" << 'ENDSSH'
set -e

# 备份 .env
if [ -f /opt/ai-trader/.env ]; then
    sudo cp /opt/ai-trader/.env /tmp/ai-trader-env-backup
fi

# 解压新代码
sudo rm -rf /opt/ai-trader/*
sudo tar -xzf /tmp/ai-trader-deploy.tgz -C /opt/ai-trader/
sudo chown -R ubuntu:ubuntu /opt/ai-trader

# 恢复 .env
if [ -f /tmp/ai-trader-env-backup ]; then
    sudo mv /tmp/ai-trader-env-backup /opt/ai-trader/.env
    sudo chown ubuntu:ubuntu /opt/ai-trader/.env
fi

# 检查并创建虚拟环境
cd /opt/ai-trader
if [ ! -d "venv" ] || [ ! -f "venv/bin/activate" ]; then
    echo "→ 创建虚拟环境..."
    python3.10 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q

# 重启服务
SVC="ai-trader"
if ! sudo systemctl is-active --quiet ai-trader; then
  if sudo systemctl is-active --quiet trigo-nexus; then
    SVC="trigo-nexus"
  fi
fi

echo "→ 重启服务: $SVC"
sudo systemctl restart $SVC
sleep 3

if sudo systemctl is-active --quiet $SVC; then
    echo "✓ 服务已成功重启"
    sudo systemctl status $SVC --no-pager | head -20
else
    echo "✗ 服务启动失败"
    sudo journalctl -u $SVC -n 30 --no-pager
    exit 1
fi
ENDSSH

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ 部署完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Edition 1: http://${EC2_IP}/edition1"
echo -e "Edition 2: http://${EC2_IP}/edition2"
echo ""
echo -e "查看日志: ssh -i $KEY_FILE $EC2_USER@$EC2_IP 'sudo journalctl -u ai-trader -f'"
echo ""

# 清理本地临时文件
rm -f /tmp/ai-trader-deploy.tgz

