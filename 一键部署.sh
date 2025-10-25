#!/bin/bash

# Trigo Nexus - Jackietomtam 专属部署脚本

echo "🚀 Trigo Nexus 一键部署"
echo "用户：Jackietomtam"
echo "=============================="
echo ""

# 检查是否在正确的目录
if [ ! -f "app_v2.py" ]; then
    echo "❌ 错误：请在项目根目录运行此脚本"
    exit 1
fi

# 步骤 1: 初始化 Git 仓库
echo "📦 步骤 1/4: 初始化 Git 仓库..."
if [ -d ".git" ]; then
    echo "✅ Git 仓库已存在"
else
    git init
    echo "✅ Git 仓库已初始化"
fi

# 步骤 2: 添加并提交所有文件
echo ""
echo "📝 步骤 2/4: 提交代码..."
git add .
git commit -m "Initial commit: Trigo Nexus AI Trading System" 2>/dev/null || echo "✅ 代码已提交（或无新更改）"

# 步骤 3: 配置远程仓库
echo ""
echo "🔗 步骤 3/4: 配置远程仓库..."
echo ""
echo "请选择操作："
echo "1. 创建新仓库 (trigo-nexus)"
echo "2. 使用已有仓库"
echo ""
read -p "请输入选项 (1 或 2): " repo_choice

if [ "$repo_choice" = "1" ]; then
    # 使用新仓库名
    REPO_NAME="trigo-nexus"
    GITHUB_URL="https://github.com/Jackietomtam/${REPO_NAME}.git"
    
    echo ""
    echo "📋 创建新仓库的步骤："
    echo "1. 访问: https://github.com/new"
    echo "2. Repository name: ${REPO_NAME}"
    echo "3. 选择 Public 或 Private"
    echo "4. ⚠️ 不要勾选 'Add a README file'"
    echo "5. 点击 'Create repository'"
    echo ""
    read -p "创建完成后，按回车继续..."
    
    # 检查是否已有远程仓库
    if git remote | grep -q "origin"; then
        git remote remove origin
    fi
    
    git remote add origin "$GITHUB_URL"
    git branch -M main
    
    echo ""
    echo "🚀 正在推送到 GitHub..."
    if git push -u origin main; then
        echo "✅ 代码已推送到 GitHub！"
    else
        echo "❌ 推送失败，请检查："
        echo "  1. GitHub 仓库是否已创建"
        echo "  2. 是否有权限访问"
        echo "  3. 网络连接是否正常"
        exit 1
    fi
elif [ "$repo_choice" = "2" ]; then
    echo ""
    read -p "请输入仓库名称: " custom_repo
    GITHUB_URL="https://github.com/Jackietomtam/${custom_repo}.git"
    
    if git remote | grep -q "origin"; then
        git remote remove origin
    fi
    
    git remote add origin "$GITHUB_URL"
    git branch -M main
    
    echo ""
    echo "🚀 正在推送到 GitHub..."
    if git push -u origin main; then
        echo "✅ 代码已推送到 GitHub！"
    else
        echo "❌ 推送失败，请检查仓库是否存在"
        exit 1
    fi
else
    echo "❌ 无效选项"
    exit 1
fi

# 步骤 4: 部署到 Railway
echo ""
echo "🚂 步骤 4/4: 部署到 Railway..."
echo ""
echo "接下来请按照以下步骤操作："
echo ""
echo "1️⃣  访问 Railway 并登录："
echo "   👉 https://railway.app"
echo "   使用 GitHub 账号 (Jackietomtam) 登录"
echo ""
echo "2️⃣  创建新项目："
echo "   - 点击 'New Project'"
echo "   - 选择 'Deploy from GitHub repo'"
echo "   - 找到并选择: Jackietomtam/${REPO_NAME:-你的仓库}"
echo ""
echo "3️⃣  配置环境变量："
echo "   进入项目设置 → Variables 标签，添加："
echo ""
echo "   OPENROUTER_API_KEY=sk-or-v1-你的OpenRouter密钥"
echo "   DASHSCOPE_API_KEY=sk-你的阿里云百炼密钥"
echo "   FINNHUB_API_KEY=你的Finnhub密钥"
echo ""
echo "4️⃣  生成域名："
echo "   Settings → Domains → Generate Domain"
echo ""
echo "5️⃣  等待部署完成（约1-2分钟）"
echo ""
echo "=============================="
echo "✅ Git 部分已完成！"
echo ""
echo "📱 快捷链接："
echo "   GitHub 仓库: https://github.com/Jackietomtam/${REPO_NAME:-你的仓库}"
echo "   Railway 部署: https://railway.app/new"
echo ""
echo "💡 提示：部署完成后，你会得到类似这样的网址："
echo "   https://trigo-nexus.up.railway.app"
echo ""
echo "🎉 祝部署顺利！"

