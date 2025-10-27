#!/bin/bash

echo "========================================"
echo "🎯 Trigo Nexus 双版本系统启动"
echo "========================================"
echo ""

# 进入项目目录
cd "$(dirname "$0")"

# 使用系统Python（miniconda3）
export PATH="/opt/miniconda3/bin:$PATH"

echo "📦 使用 Python 环境: $(which python)"
echo "📦 Python 版本: $(python --version)"

echo ""
echo "========================================="
echo "✅ 启动双版本系统"
echo "========================================="
echo ""
echo "📍 主页: http://localhost:5001/"
echo "📍 Edition 1 (原版): http://localhost:5001/edition1"
echo "📍 Edition 2 (带新闻): http://localhost:5001/edition2"
echo "📍 模型对比: http://localhost:5001/models"
echo "📍 模型对比(新): http://localhost:5001/models_new"
echo ""
echo "========================================="
echo ""

# 启动应用
python app_dual_edition.py







