#!/bin/bash

# 部署 margin_used 修复到 AWS 服务器
# 使用方法: bash deploy_to_aws_margin_fix.sh

echo ""
echo "========================================================================"
echo "🚀 部署 margin_used 修复到 AWS 服务器"
echo "========================================================================"
echo ""

# 服务器信息
SERVER_IP="3.106.191.40"
SERVER_USER="ubuntu"
KEY_PATH="~/Downloads/trigo-key.pem"

echo "📋 服务器信息:"
echo "   IP: $SERVER_IP"
echo "   用户: $SERVER_USER"
echo ""

# 检查密钥文件
if [ ! -f "$KEY_PATH" ]; then
    echo "⚠️  密钥文件不存在: $KEY_PATH"
    echo ""
    read -p "请输入正确的密钥文件路径: " KEY_PATH
    if [ ! -f "$KEY_PATH" ]; then
        echo "❌ 密钥文件仍然不存在，退出部署"
        exit 1
    fi
fi

echo "✅ 找到密钥文件: $KEY_PATH"
echo ""

# SSH到服务器并执行部署
echo "🔐 连接到服务器..."
ssh -i "$KEY_PATH" $SERVER_USER@$SERVER_IP << 'ENDSSH'

echo ""
echo "================================"
echo "📥 步骤1: 拉取最新代码"
echo "================================"
cd Trigo-Nexus || cd AI交易 || { echo "❌ 找不到项目目录"; exit 1; }
echo "当前目录: $(pwd)"

git pull origin main

echo ""
echo "================================"
echo "🔍 步骤2: 验证修复文件"
echo "================================"
if [ -f "leverage_engine.py" ]; then
    if grep -q "fix_margin_used_all" leverage_engine.py; then
        echo "✅ leverage_engine.py 包含修复代码"
    else
        echo "⚠️  leverage_engine.py 可能未更新"
    fi
fi

if [ -f "check_margin_used.py" ]; then
    echo "✅ 测试工具 check_margin_used.py 存在"
else
    echo "⚠️  测试工具不存在"
fi

if [ -f "QUICK_FIX_GUIDE.md" ]; then
    echo "✅ 部署指南存在"
fi

echo ""
echo "================================"
echo "📊 步骤3: 检查当前服务状态"
echo "================================"
if sudo systemctl status trigo-nexus --no-pager 2>/dev/null | head -5; then
    SERVICE_NAME="trigo-nexus"
elif sudo systemctl status ai-trader --no-pager 2>/dev/null | head -5; then
    SERVICE_NAME="ai-trader"
else
    echo "⚠️  未找到 systemd 服务"
    SERVICE_NAME=""
fi

echo ""
echo "================================"
echo "🔄 步骤4: 重启服务"
echo "================================"

if [ -n "$SERVICE_NAME" ]; then
    echo "重启服务: $SERVICE_NAME"
    sudo systemctl restart $SERVICE_NAME
    echo "✅ 服务重启成功"
    sleep 3
    
    echo ""
    echo "📋 查看启动日志..."
    sudo journalctl -u $SERVICE_NAME -n 50 --no-pager | tail -30
    
    echo ""
    echo "🔍 查找修复日志..."
    sudo journalctl -u $SERVICE_NAME -n 100 --no-pager | grep -E "修复|margin_used|fix_margin" | tail -10
else
    echo "使用手动方式重启..."
    pkill -f app_dual_edition.py || pkill -f app_v2.py
    sleep 2
    
    # 启动服务
    if [ -f "app_dual_edition.py" ]; then
        nohup python3 app_dual_edition.py > app.log 2>&1 &
        echo "✅ app_dual_edition.py 已启动"
    elif [ -f "app_v2.py" ]; then
        nohup python3 app_v2.py > app.log 2>&1 &
        echo "✅ app_v2.py 已启动"
    fi
    
    sleep 3
    
    echo ""
    echo "📋 查看启动日志..."
    if [ -f "app.log" ]; then
        tail -30 app.log
        
        echo ""
        echo "🔍 查找修复日志..."
        grep -E "修复|margin_used|fix_margin" app.log | tail -10
    fi
fi

echo ""
echo "================================"
echo "✅ 部署完成！"
echo "================================"
echo ""
echo "📊 验证步骤："
echo "1. 访问网站: http://trigoai.site"
echo "2. 查看 Edition 1 的 Available Cash"
echo "3. 应该从 \$18.65 恢复到 ~\$98,567"
echo ""
echo "🔍 持续监控："
if [ -n "$SERVICE_NAME" ]; then
    echo "   sudo journalctl -u $SERVICE_NAME -f"
else
    echo "   tail -f app.log"
fi
echo ""
echo "💡 如果需要查看更多日志:"
if [ -n "$SERVICE_NAME" ]; then
    echo "   sudo journalctl -u $SERVICE_NAME -n 100"
else
    echo "   tail -100 app.log"
fi

ENDSSH

echo ""
echo "========================================================================"
echo "🎉 部署脚本执行完成！"
echo "========================================================================"
echo ""
echo "📋 下一步："
echo "1. 打开浏览器访问: http://trigoai.site"
echo "2. 查看 Available Cash 是否恢复正常"
echo "3. 如果显示正常，说明修复成功！"
echo ""

