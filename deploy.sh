#!/bin/bash

# Trigo Nexus 部署准备脚本

echo "🚀 Trigo Nexus 部署准备工具"
echo "=============================="
echo ""

# 检查必要文件
echo "📋 检查必要文件..."
files=("requirements.txt" "Procfile" ".gitignore" "app_v2.py" "config.py")
all_good=true

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file 缺失！"
        all_good=false
    fi
done

echo ""

if [ "$all_good" = false ]; then
    echo "❌ 有文件缺失，请检查！"
    exit 1
fi

# 检查 Git 仓库
echo "🔍 检查 Git 仓库..."
if [ -d ".git" ]; then
    echo "✅ Git 仓库已存在"
else
    echo "⚠️  还没有初始化 Git 仓库"
    echo "是否现在初始化？(y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        git init
        git add .
        git commit -m "Initial commit: Trigo Nexus AI Trading System"
        echo "✅ Git 仓库已初始化"
    fi
fi

echo ""

# 检查环境变量
echo "🔑 检查 API 密钥..."
if grep -q "your_.*_key_here" config.py 2>/dev/null; then
    echo "⚠️  警告：config.py 中包含示例密钥"
    echo "建议：将真实密钥移到环境变量中"
fi

echo ""

# 提供部署选项
echo "📦 选择部署平台："
echo "1. Railway (推荐 - 最简单)"
echo "2. Render (免费)"
echo "3. Heroku"
echo "4. VPS (自己的服务器)"
echo "5. 查看完整部署指南"
echo ""
echo "请输入数字 (1-5):"
read -r choice

case $choice in
    1)
        echo ""
        echo "🚂 Railway 部署步骤："
        echo "1. 访问 https://railway.app"
        echo "2. 使用 GitHub 登录"
        echo "3. 点击 'New Project' → 'Deploy from GitHub repo'"
        echo "4. 选择你的仓库"
        echo "5. 添加环境变量（在项目设置中）："
        echo "   OPENROUTER_API_KEY=你的密钥"
        echo "   DASHSCOPE_API_KEY=你的密钥"
        echo "   FINNHUB_API_KEY=你的密钥"
        echo ""
        echo "详细步骤请查看：部署指南.md"
        ;;
    2)
        echo ""
        echo "🎨 Render 部署步骤："
        echo "1. 访问 https://render.com"
        echo "2. 使用 GitHub 登录"
        echo "3. 点击 'New +' → 'Web Service'"
        echo "4. 连接你的仓库"
        echo "5. 配置："
        echo "   - Build Command: pip install -r requirements.txt"
        echo "   - Start Command: gunicorn --worker-class eventlet -w 1 app_v2:app --bind 0.0.0.0:\$PORT"
        echo "6. 添加环境变量"
        echo ""
        echo "详细步骤请查看：部署指南.md"
        ;;
    3)
        echo ""
        echo "🟣 Heroku 部署步骤："
        echo "1. 安装 Heroku CLI:"
        echo "   brew install heroku/brew/heroku"
        echo "2. 登录并创建应用："
        echo "   heroku login"
        echo "   heroku create trigo-nexus"
        echo "3. 配置环境变量："
        echo "   heroku config:set OPENROUTER_API_KEY=你的密钥"
        echo "   heroku config:set DASHSCOPE_API_KEY=你的密钥"
        echo "4. 部署："
        echo "   git push heroku main"
        echo ""
        echo "详细步骤请查看：部署指南.md"
        ;;
    4)
        echo ""
        echo "🖥️  VPS 部署比较复杂，请查看详细文档："
        echo "打开：部署指南.md"
        echo ""
        echo "推荐服务商："
        echo "- Vultr: https://vultr.com (\$5/月起)"
        echo "- DigitalOcean: https://digitalocean.com (\$4/月起)"
        echo "- 阿里云: https://aliyun.com (学生机 9.9元/月)"
        ;;
    5)
        echo ""
        echo "📖 正在打开部署指南..."
        if command -v open &> /dev/null; then
            open "部署指南.md"
        elif command -v xdg-open &> /dev/null; then
            xdg-open "部署指南.md"
        else
            echo "请手动打开文件：部署指南.md"
        fi
        ;;
    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac

echo ""
echo "✅ 准备完成！"
echo ""
echo "下一步："
echo "1. 确保代码已推送到 GitHub"
echo "2. 在部署平台连接你的仓库"
echo "3. 配置环境变量（API 密钥）"
echo "4. 部署！"
echo ""
echo "需要帮助？查看：部署指南.md"

