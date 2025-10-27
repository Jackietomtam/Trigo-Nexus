#!/bin/bash
cd "$(dirname "$0")"

echo "========================================="
echo "🚀 启动 Trigo Nexus 本地测试"
echo "========================================="
echo ""

# 检查虚拟环境
if [ ! -d "venv_local" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv_local
    echo "✅ 虚拟环境创建成功！"
    echo ""
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv_local/bin/activate

# 安装依赖
echo "📥 检查并安装依赖..."
pip install -r requirements.txt -q

echo ""
echo "========================================="
echo "🚀 启动应用..."
echo "========================================="
echo ""
echo "📍 访问地址: http://localhost:5001"
echo "📊 实时AI交易竞赛正在运行..."
echo "⚠️  按 Ctrl+C 停止服务"
echo ""
echo "========================================="
echo ""

# 启动应用
python app_v2.py
