#!/bin/bash
set -e

# AWS EC2 配置
EC2_IP="3.106.191.40"
EC2_USER="ubuntu"
KEY_FILE="$HOME/Downloads/trigo-key.pem"
REMOTE_DIR="/opt/ai-trader"
LOCAL_DIR="$(cd "$(dirname "$0")" && pwd)"

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}🚀 部署最新代码到 AWS${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 检查密钥
if [ ! -f "$KEY_FILE" ]; then
    echo "❌ 找不到密钥: $KEY_FILE"
    exit 1
fi
chmod 400 "$KEY_FILE"

# 1. 上传代码
echo -e "${YELLOW}📤 Step 1/3: 上传代码...${NC}"
ssh -i "$KEY_FILE" "$EC2_USER@$EC2_IP" "sudo rm -rf /tmp/ai-trader-upload"
scp -i "$KEY_FILE" -r "$LOCAL_DIR" "$EC2_USER@$EC2_IP:/tmp/ai-trader-upload"
echo -e "${GREEN}✅ 代码已上传${NC}"
echo ""

# 2. 替换文件并保留 .env
echo -e "${YELLOW}⚙️  Step 2/3: 更新应用文件...${NC}"
ssh -i "$KEY_FILE" "$EC2_USER@$EC2_IP" << 'ENDSSH'
set -e
# 备份 .env
if [ -f /opt/ai-trader/.env ]; then
    sudo cp /opt/ai-trader/.env /tmp/ai-trader-env-backup
fi

# 清理并移动新代码
sudo rm -rf /opt/ai-trader/*
sudo mv /tmp/ai-trader-upload/* /opt/ai-trader/
sudo chown -R ubuntu:ubuntu /opt/ai-trader

# 恢复 .env
if [ -f /tmp/ai-trader-env-backup ]; then
    sudo mv /tmp/ai-trader-env-backup /opt/ai-trader/.env
    sudo chown ubuntu:ubuntu /opt/ai-trader/.env
fi

echo "✓ 文件已更新"
ENDSSH
echo -e "${GREEN}✅ 应用文件已更新${NC}"
echo ""

# 3. 安装依赖并重启
echo -e "${YELLOW}🔄 Step 3/3: 安装依赖并重启服务...${NC}"
ssh -i "$KEY_FILE" "$EC2_USER@$EC2_IP" << 'ENDSSH'
set -e
cd /opt/ai-trader
source venv/bin/activate
pip install -r requirements.txt -q

# 确定服务名
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
else
    echo "✗ 服务启动失败，查看日志:"
    sudo journalctl -u $SVC -n 30 --no-pager
    exit 1
fi
ENDSSH

# 完成
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ 部署完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}📍 访问地址:${NC}"
echo -e "   Edition 1: ${GREEN}http://${EC2_IP}/edition1${NC}"
echo -e "   Edition 2: ${GREEN}http://${EC2_IP}/edition2${NC}"
echo ""
echo -e "${BLUE}📊 查看日志:${NC}"
echo -e "   ${GREEN}ssh -i $KEY_FILE $EC2_USER@$EC2_IP 'sudo journalctl -u ai-trader -f'${NC}"
echo ""
echo -e "${YELLOW}✨ 本次更新包含:${NC}"
echo "   • Binance 优先，Finnhub/CoinGecko 兜底"
echo "   • 拦截零数量持仓，修复 MKT VALUE=0"
echo "   • 历史K线多源容错"
echo ""


