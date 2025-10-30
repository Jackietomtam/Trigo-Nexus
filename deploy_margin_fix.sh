#!/bin/bash

# 部署 margin_used 修复
# 使用方法: bash deploy_margin_fix.sh

set -e  # 遇到错误立即退出

echo ""
echo "========================================================================"
echo "🔧 Margin Used Bug 修复部署"
echo "========================================================================"
echo ""

# 检查是否在正确的目录
if [ ! -f "leverage_engine.py" ]; then
    echo "❌ 错误：请在项目根目录运行此脚本"
    exit 1
fi

# 步骤1: 验证修复
echo "📝 步骤1：运行测试验证..."
echo "----------------------------------------"
python3 check_margin_used.py
echo ""

read -p "测试是否通过？继续部署？(y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ 部署取消"
    exit 1
fi

# 步骤2: 备份（如果需要）
echo ""
echo "📦 步骤2：备份文件..."
echo "----------------------------------------"
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp leverage_engine.py "$BACKUP_DIR/"
cp app_dual_edition.py "$BACKUP_DIR/"
echo "✅ 备份已保存到: $BACKUP_DIR"

# 步骤3: 检查进程
echo ""
echo "🔍 步骤3：检查运行中的进程..."
echo "----------------------------------------"
if pgrep -f "app_dual_edition.py" > /dev/null; then
    echo "⚠️  发现运行中的 app_dual_edition.py 进程"
    ps aux | grep "app_dual_edition.py" | grep -v grep
    echo ""
    read -p "是否需要重启进程？(y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🛑 停止旧进程..."
        pkill -f app_dual_edition.py || true
        sleep 2
        echo "✅ 进程已停止"
        
        echo ""
        echo "🚀 启动新进程..."
        nohup python3 app_dual_edition.py > app.log 2>&1 &
        sleep 3
        echo "✅ 新进程已启动"
        
        echo ""
        echo "📋 查看启动日志（最后30行）："
        echo "----------------------------------------"
        tail -n 30 app.log
    fi
else
    echo "✅ 没有运行中的进程"
fi

# 步骤4: 验证结果
echo ""
echo "========================================================================"
echo "✅ 部署完成！"
echo "========================================================================"
echo ""
echo "📋 后续步骤："
echo ""
echo "1. 查看日志中的修复信息："
echo "   tail -f app.log | grep '🔧'"
echo ""
echo "2. 检查前端显示："
echo "   - 打开浏览器访问系统"
echo "   - 查看 Edition 1 的 Available Cash"
echo "   - 应该从 \$18.65 恢复到 ~\$98,567"
echo ""
echo "3. 持续监控："
echo "   grep '🔧 \[修复\]' app.log"
echo "   (如果持续出现修复日志，说明有其他bug)"
echo ""
echo "4. 如果需要回滚："
echo "   cp $BACKUP_DIR/leverage_engine.py ."
echo "   cp $BACKUP_DIR/app_dual_edition.py ."
echo "   pkill -f app_dual_edition.py"
echo "   python3 app_dual_edition.py"
echo ""
echo "========================================================================"

