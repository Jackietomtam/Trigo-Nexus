# 🔧 修复 GitHub 认证问题

3种简单方法，选一个即可！

---

## ⚡ 方法 1: 使用 GitHub Desktop (最简单) ⭐⭐⭐⭐⭐

### 1. 下载并安装 GitHub Desktop
- 访问：https://desktop.github.com
- 下载并安装

### 2. 登录 GitHub Desktop
- 打开应用
- 用 Jackietomtam 账号登录

### 3. 添加项目
1. File → Add Local Repository
2. 选择：`/Users/sogmac/Desktop/Agent-Test/AI交易`
3. 点击 "Add Repository"

### 4. 创建 GitHub 仓库并推送
1. 点击 "Publish repository"
2. 填写：
   - Name: `trigo-nexus`
   - Description: AI Trading System
   - 取消勾选 "Keep this code private"（或保持勾选）
3. 点击 "Publish Repository"

✅ **完成！代码已推送到 GitHub**

### 5. 部署到 Railway
- 访问：https://railway.app
- New Project → Deploy from GitHub repo
- 选择：Jackietomtam/trigo-nexus

---

## 🔑 方法 2: 使用 Personal Access Token

### 1. 创建 GitHub Token
1. 访问：https://github.com/settings/tokens
2. 点击 "Generate new token (classic)"
3. 填写：
   - Note: `Railway Deploy`
   - Expiration: `90 days`
   - 勾选权限：`repo` (完整勾选)
4. 点击 "Generate token"
5. **复制 token**（只显示一次！）

### 2. 使用 Token 推送
```bash
cd "/Users/sogmac/Desktop/Agent-Test/AI交易"

# 先在 GitHub 网页创建仓库：
# https://github.com/new
# 仓库名：trigo-nexus

# 使用 token 推送（用 token 替换密码）
git remote remove origin
git remote add origin https://Jackietomtam:你的token@github.com/Jackietomtam/trigo-nexus.git
git push -u origin main
```

---

## 🔐 方法 3: 使用 SSH 密钥

### 1. 生成 SSH 密钥
```bash
ssh-keygen -t ed25519 -C "你的邮箱@example.com"
```
连按3次回车（使用默认设置）

### 2. 添加到 GitHub
```bash
# 复制公钥
cat ~/.ssh/id_ed25519.pub | pbcopy
```

1. 访问：https://github.com/settings/keys
2. 点击 "New SSH key"
3. Title: `Mac`
4. Key: 粘贴刚复制的内容
5. 点击 "Add SSH key"

### 3. 测试连接
```bash
ssh -T git@github.com
```

### 4. 推送代码
```bash
cd "/Users/sogmac/Desktop/Agent-Test/AI交易"

# 先在 GitHub 网页创建仓库

# 使用 SSH 推送
git remote remove origin
git remote add origin git@github.com:Jackietomtam/trigo-nexus.git
git push -u origin main
```

---

## 🎯 推荐顺序

1. **GitHub Desktop** - 最简单，零配置 ⭐⭐⭐⭐⭐
2. **Railway CLI** - 无需 GitHub，直接部署 ⭐⭐⭐⭐
3. **Personal Token** - 快速但需要管理 token ⭐⭐⭐
4. **SSH 密钥** - 一次配置，永久使用 ⭐⭐⭐⭐

---

## 📞 遇到问题？

### GitHub Desktop 找不到仓库？
- 检查路径是否正确
- 确认 Git 仓库已初始化（有 `.git` 文件夹）

### Token 推送还是失败？
- 检查 token 是否正确复制
- 确认 token 有 `repo` 权限

### SSH 连接失败？
- 检查公钥是否正确添加到 GitHub
- 运行 `ssh -T git@github.com` 测试

---

**推荐：使用 GitHub Desktop，3分钟搞定！** 🚀

