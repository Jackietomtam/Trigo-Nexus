#!/bin/bash
# 快速部署 Available Cash 修复
# 使用方法: chmod +x quick_fix_deploy.sh && ./quick_fix_deploy.sh

set -e  # 遇到错误立即退出

echo "🚀 开始部署 Available Cash 修复..."
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 服务器信息
SERVER="ubuntu@3.106.191.40"
KEY_PATH="$HOME/Downloads/trigo-key.pem"
PROJECT_DIR="/home/ubuntu/AI交易"

# 检查 SSH 密钥
if [ ! -f "$KEY_PATH" ]; then
    echo -e "${RED}❌ SSH 密钥不存在: $KEY_PATH${NC}"
    echo "请确保密钥文件路径正确"
    exit 1
fi

echo -e "${GREEN}✓${NC} SSH 密钥检查通过"

# 步骤 1: 测试连接
echo ""
echo "📡 测试服务器连接..."
if ssh -i "$KEY_PATH" -o ConnectTimeout=5 "$SERVER" "echo '连接成功'" > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} 服务器连接正常"
else
    echo -e "${RED}❌ 无法连接到服务器${NC}"
    exit 1
fi

# 步骤 2: 备份当前状态
echo ""
echo "💾 备份当前代码..."
ssh -i "$KEY_PATH" "$SERVER" << 'ENDSSH'
cd /home/ubuntu/AI交易
# 创建备份分支
BACKUP_BRANCH="backup-$(date +%Y%m%d-%H%M%S)"
git branch "$BACKUP_BRANCH" 2>/dev/null || true
echo "备份分支: $BACKUP_BRANCH"
ENDSSH

echo -e "${GREEN}✓${NC} 备份完成"

# 步骤 3: 拉取最新代码
echo ""
echo "📥 拉取最新修复代码..."
ssh -i "$KEY_PATH" "$SERVER" << 'ENDSSH'
cd /home/ubuntu/AI交易

# 保存本地修改
git stash save "auto-stash-before-fix-$(date +%Y%m%d-%H%M%S)" 2>/dev/null || true

# 拉取最新代码
if git pull origin main; then
    echo "✓ 代码更新成功"
else
    echo "⚠ 代码拉取失败，尝试强制更新..."
    git fetch origin
    git reset --hard origin/main
fi

# 显示最新提交
echo ""
echo "最新提交:"
git log --oneline -3
ENDSSH

echo -e "${GREEN}✓${NC} 代码更新完成"

# 步骤 4: 验证修复文件
echo ""
echo "🔍 验证修复文件..."
ssh -i "$KEY_PATH" "$SERVER" << 'ENDSSH'
cd /home/ubuntu/AI交易

echo "检查关键修复..."

# 检查 leverage_engine.py
if grep -q "if available_cash < 0:" leverage_engine.py; then
    echo "✓ leverage_engine.py 已修复"
else
    echo "⚠ leverage_engine.py 可能未正确修复"
fi

# 检查 ai_trader_v2.py
if grep -q "min_notional_usd = 50.0" ai_trader_v2.py; then
    echo "✓ ai_trader_v2.py 已修复"
else
    echo "⚠ ai_trader_v2.py 可能未正确修复"
fi

# 检查 app_dual_edition.py
if grep -q "min_notional_usd = 50.0" app_dual_edition.py; then
    echo "✓ app_dual_edition.py 已修复"
else
    echo "⚠ app_dual_edition.py 可能未正确修复"
fi
ENDSSH

# 步骤 5: 重启服务
echo ""
echo "🔄 重启 Trigo Nexus 服务..."
ssh -i "$KEY_PATH" "$SERVER" << 'ENDSSH'
# 重启服务
sudo systemctl restart trigo-ai-trader

# 等待 3 秒
sleep 3

# 检查状态
if sudo systemctl is-active --quiet trigo-ai-trader; then
    echo "✓ 服务启动成功"
    sudo systemctl status trigo-ai-trader --no-pager -l | head -15
else
    echo "❌ 服务启动失败"
    echo "查看错误日志:"
    sudo journalctl -u trigo-ai-trader -n 50 --no-pager
    exit 1
fi
ENDSSH

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} 服务重启成功"
else
    echo -e "${RED}❌ 服务重启失败${NC}"
    exit 1
fi

# 步骤 6: 实时日志（10秒）
echo ""
echo "📋 查看实时日志（10秒）..."
echo -e "${YELLOW}按 Ctrl+C 可提前退出${NC}"
echo ""

ssh -i "$KEY_PATH" "$SERVER" << 'ENDSSH'
timeout 10 sudo journalctl -u trigo-ai-trader -f 2>/dev/null || sudo journalctl -u trigo-ai-trader -n 30
ENDSSH

# 步骤 7: 验证修复效果
echo ""
echo "🎯 验证修复效果..."
ssh -i "$KEY_PATH" "$SERVER" << 'ENDSSH'
cd /home/ubuntu/AI交易

echo ""
echo "检查最近的日志标志..."

# 检查是否有"名义金额不足"的日志（说明阈值生效）
if sudo journalctl -u trigo-ai-trader -n 200 --no-pager | grep -q "名义金额不足"; then
    echo "✓ 最小名义金额阈值已生效"
else
    echo "ℹ 尚未看到名义金额不足的日志（可能是资金充足）"
fi

# 检查是否有 AI 决策日志
if sudo journalctl -u trigo-ai-trader -n 200 --no-pager | grep -q "开始AI决策"; then
    echo "✓ AI 决策系统正常运行"
else
    echo "⚠ 未检测到 AI 决策日志"
fi

# 检查是否有错误
ERROR_COUNT=$(sudo journalctl -u trigo-ai-trader -n 200 --no-pager | grep -i "error\|exception\|traceback" | wc -l)
if [ "$ERROR_COUNT" -gt 0 ]; then
    echo "⚠ 发现 $ERROR_COUNT 条错误日志，建议检查"
else
    echo "✓ 无错误日志"
fi
ENDSSH

# 完成
echo ""
echo "=========================================="
echo -e "${GREEN}🎉 部署完成！${NC}"
echo "=========================================="
echo ""
echo "📊 验证步骤:"
echo "1. 访问 Edition 1: http://3.106.191.40:5001/edition1"
echo "2. 访问 Edition 2: http://3.106.191.40:5001/edition2"
echo ""
echo "✅ 检查项目:"
echo "  • Available Cash 不再显示 \$0.00"
echo "  • 持仓 Quantity 显示 6 位小数（非 0.0000）"
echo "  • 图表随市场波动（非水平直线）"
echo ""
echo "📋 查看实时日志:"
echo "  ssh -i $KEY_PATH $SERVER"
echo "  sudo journalctl -u trigo-ai-trader -f"
echo ""
echo "🔙 如需回滚:"
echo "  ssh -i $KEY_PATH $SERVER"
echo "  cd $PROJECT_DIR"
echo "  git reset --hard HEAD~1"
echo "  sudo systemctl restart trigo-ai-trader"
echo ""

