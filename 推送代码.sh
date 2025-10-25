#!/bin/bash

# 使用 Token 推送代码到 GitHub

echo "🚀 推送代码到 GitHub"
echo "===================="
echo ""

# 获取 Token
echo "请粘贴你的 GitHub Token (以 ghp_ 开头):"
read -r TOKEN

if [[ ! $TOKEN =~ ^ghp_ ]]; then
    echo "❌ Token 格式不正确！应该以 ghp_ 开头"
    exit 1
fi

echo ""
echo "✅ Token 已接收"
echo "📤 开始推送..."
echo ""

cd "/Users/sogmac/Desktop/Agent-Test/AI交易"

# 移除旧的远程仓库
git remote remove origin 2>/dev/null

# 添加新的远程仓库（使用 Token）
git remote add origin https://Jackietomtam:${TOKEN}@github.com/Jackietomtam/trigo-nexus.git

# 推送
if git push -u origin main; then
    echo ""
    echo "=============================="
    echo "✅ 代码已成功推送到 GitHub！"
    echo ""
    echo "📦 GitHub 仓库地址："
    echo "   https://github.com/Jackietomtam/trigo-nexus"
    echo ""
    echo "🚂 下一步：部署到 Railway"
    echo "   1. 访问: https://railway.app"
    echo "   2. 登录并创建新项目"
    echo "   3. 选择: Deploy from GitHub repo"
    echo "   4. 选择: Jackietomtam/trigo-nexus"
    echo "   5. 添加环境变量（API密钥）"
    echo "   6. 生成域名"
    echo ""
    echo "🎉 准备部署到 Railway？"
    echo ""
    
    # 询问是否打开 Railway
    read -p "是否现在打开 Railway? (y/n): " open_railway
    if [[ "$open_railway" =~ ^[Yy]$ ]]; then
        open "https://railway.app/new"
    fi
else
    echo ""
    echo "❌ 推送失败！"
    echo "请检查："
    echo "  1. GitHub 仓库是否已创建"
    echo "  2. Token 是否有效"
    echo "  3. 网络连接是否正常"
fi

