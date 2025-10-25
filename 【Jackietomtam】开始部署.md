# 🚀 Jackietomtam - 开始部署 Trigo Nexus

专属部署指南

---

## ⚡ 最快方式：一键部署脚本

打开终端，运行：

```bash
cd "/Users/sogmac/Desktop/Agent-Test/AI交易"
./一键部署.sh
```

脚本会自动帮你完成：
- ✅ 初始化 Git 仓库
- ✅ 提交所有代码
- ✅ 推送到 GitHub
- ✅ 给你部署步骤指引

---

## 📝 手动部署（分步说明）

### 步骤 1: 推送代码到 GitHub

#### 1.1 初始化 Git
```bash
cd "/Users/sogmac/Desktop/Agent-Test/AI交易"
git init
git add .
git commit -m "Initial commit: Trigo Nexus"
```

#### 1.2 创建 GitHub 仓库
1. 访问：https://github.com/new
2. 填写信息：
   - **Repository name**: `trigo-nexus`
   - **Description**: AI Trading System
   - **Visibility**: Public 或 Private（推荐 Private）
   - ⚠️ **不要勾选** "Add a README file"
3. 点击 **"Create repository"**

#### 1.3 推送代码
```bash
git remote add origin https://github.com/Jackietomtam/trigo-nexus.git
git branch -M main
git push -u origin main
```

✅ **完成后**，你的代码会出现在：
https://github.com/Jackietomtam/trigo-nexus

---

### 步骤 2: 部署到 Railway

#### 2.1 登录 Railway
1. 访问：https://railway.app
2. 点击右上角 **"Login"**
3. 选择 **"Login with GitHub"**
4. 使用你的 GitHub 账号 (Jackietomtam) 登录

#### 2.2 创建新项目
1. 点击 **"New Project"**
2. 选择 **"Deploy from GitHub repo"**
3. 在列表中找到：**Jackietomtam/trigo-nexus**
4. 点击仓库名开始部署

Railway 会自动：
- ✅ 检测到 Python 项目
- ✅ 读取 `requirements.txt`
- ✅ 安装依赖
- ✅ 使用 `Procfile` 启动应用

#### 2.3 配置环境变量（重要！）
在 Railway 项目页面：

1. 点击项目卡片
2. 切换到 **"Variables"** 标签
3. 点击 **"New Variable"**
4. 添加以下 3 个变量：

| 变量名 | 值 | 说明 |
|-------|-----|------|
| `OPENROUTER_API_KEY` | `sk-or-v1-你的密钥` | DeepSeek AI |
| `DASHSCOPE_API_KEY` | `sk-你的密钥` | Qwen3 AI |
| `FINNHUB_API_KEY` | `你的密钥` | 市场数据（可选） |

**获取 API 密钥：**
- OpenRouter: https://openrouter.ai/keys
- 阿里云百炼: https://bailian.console.aliyun.com/
- Finnhub: https://finnhub.io/register

#### 2.4 生成域名
1. 在项目页面，进入 **"Settings"** 标签
2. 找到 **"Domains"** 部分
3. 点击 **"Generate Domain"**

你会得到一个域名，类似：
```
https://trigo-nexus.up.railway.app
```

#### 2.5 等待部署完成
- 查看 **"Deployments"** 标签
- 等待状态变为 **"Success"** （约1-2分钟）
- 点击域名访问你的网站！

---

## 🎉 部署完成！

你的 AI 交易系统已经上线了！

### 访问地址：
```
https://trigo-nexus.up.railway.app
（你的实际域名）
```

### 功能检查：
- [ ] 首页能正常打开
- [ ] 看到两个 AI 卡片（Qwen3 MAX 和 DeepSeek V3.2）
- [ ] 价格数据实时更新
- [ ] 图表正常显示
- [ ] 可以点击 AI 卡片查看详情

---

## 🔧 常用操作

### 查看日志
1. 进入 Railway 项目
2. 点击 **"Deployments"**
3. 点击最新的部署
4. 查看 **"View Logs"**

### 更新代码
当你修改代码后：
```bash
cd "/Users/sogmac/Desktop/Agent-Test/AI交易"
git add .
git commit -m "更新描述"
git push
```
Railway 会自动重新部署！

### 暂停/恢复
- Railway 项目设置 → **"Pause Service"**
- 免费额度用完时，可以暂停不需要的服务

### 绑定自定义域名
1. Railway 项目 → Settings → Domains
2. 点击 **"Custom Domain"**
3. 输入你的域名（如 `ai.jackietomtam.com`）
4. 在域名服务商添加 CNAME 记录

---

## 📊 免费额度说明

Railway 免费计划：
- ✅ **$5 免费额度/月**
- ✅ **500 小时运行时间/月**
- ✅ 自动 HTTPS
- ✅ 无限部署次数

**足够轻度使用！** 如果额度用完，可以：
1. 升级到 Hobby 计划（$5/月）
2. 使用其他平台（Render 免费）
3. 等待下月重置

---

## 🐛 遇到问题？

### 问题 1: git push 失败
**解决**：
```bash
# 检查远程仓库是否正确
git remote -v

# 重新设置
git remote remove origin
git remote add origin https://github.com/Jackietomtam/trigo-nexus.git
git push -u origin main
```

### 问题 2: Railway 部署失败
**检查**：
1. 日志中的错误信息
2. 环境变量是否配置正确
3. API 密钥是否有效

### 问题 3: AI 不工作
**检查**：
1. 环境变量中的 API 密钥格式是否正确
2. API 密钥是否有效且有额度
3. 查看 Railway 日志中的错误

### 问题 4: 网站很慢
**原因**：
- Railway 免费版性能有限
- AI 调用需要时间

**解决**：
- 等待几秒钟
- 考虑升级到付费版
- 使用 VPS（性能更好）

---

## 🎯 下一步

### 分享你的网站
```
我的 AI 交易系统：
https://trigo-nexus.up.railway.app

GitHub 仓库：
https://github.com/Jackietomtam/trigo-nexus
```

### 优化建议
- 绑定自定义域名
- 添加访问统计
- 设置监控告警
- 备份重要数据

---

## 📞 获取帮助

- **Railway 文档**: https://docs.railway.app
- **部署问题**: 查看 `部署指南.md`
- **快速入门**: 运行 `./一键部署.sh`

---

## ✨ 快速链接

| 资源 | 链接 |
|------|------|
| **你的 GitHub** | https://github.com/Jackietomtam |
| **项目仓库** | https://github.com/Jackietomtam/trigo-nexus |
| **Railway 控制台** | https://railway.app/dashboard |
| **部署脚本** | `./一键部署.sh` |

---

**准备好了吗？运行部署脚本开始：**

```bash
./一键部署.sh
```

**祝部署顺利！🚀**

