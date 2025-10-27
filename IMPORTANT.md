# 🔐 Trigo Nexus - 重要信息汇总

> ⚠️ **本文件包含敏感信息，请勿公开分享！**
> 
> **最后更新**：2025-10-26

---

## 📋 目录

1. [API密钥](#api密钥)
2. [GitHub信息](#github信息)
3. [AWS服务器信息](#aws服务器信息)
4. [域名信息](#域名信息)
5. [Google Search Console](#google-search-console)
6. [快速部署命令](#快速部署命令)
7. [重要文件说明](#重要文件说明)
8. [紧急恢复指南](#紧急恢复指南)

---

## 🔑 API密钥

### OpenRouter API（备用，如需使用）
```
API Key: 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
用途: 通用AI模型API
文档: https://openrouter.ai/docs
```

### 阿里云百炼 DashScope API（主要使用）

#### Qwen3 API
```
API Key: sk-79529efd5f434d8aa9eea08c17441096
用途: Qwen3 MAX 模型
模型名: qwen3-max
端点: https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions
文档: https://help.aliyun.com/zh/dashscope
```

#### DeepSeek API
```
API Key: sk-f4168a5a023345afb1ce334f25b77365
用途: DeepSeek V3.2 模型
模型名: deepseek-v3.2-exp
端点: https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions
特性: 支持思考模式（enable_thinking）
```

### Finnhub API（市场数据）
```
API Key: d1ivl31r01qhbuvsiufgd1ivl31r01qhbuvsiug0
用途: 加密货币实时价格和24小时涨跌幅
限制: 免费版60次/分钟
文档: https://finnhub.io/docs/api
端点: https://finnhub.io/api/v1/quote
```

### Binance API（K线数据）
```
用途: 历史K线数据和技术指标计算
特点: 无需API Key，公开端点
端点: https://api.binance.com/api/v3/klines
备用端点: api1.binance.com, api2.binance.com, api3.binance.com, api4.binance.com
```

---

## 💻 GitHub信息

### 仓库信息
```
仓库名: Trigo-Nexus
用户名: Jackietomtam
仓库URL: https://github.com/Jackietomtam/Trigo-Nexus
可见性: Private（私有仓库）
```

### Git配置
```bash
# 查看当前配置
git config --list

# 如果需要重新配置用户信息
git config --global user.name "Jackietomtam"
git config --global user.email "your-email@example.com"
```

### 常用Git命令
```bash
# 查看状态
git status

# 提交更改
git add .
git commit -m "更新说明"
git push

# 拉取最新代码
git pull

# 查看提交历史
git log --oneline
```

---

## ☁️ AWS服务器信息

### EC2实例
```
区域: Asia Pacific (Sydney) ap-southeast-2
实例类型: t2.micro
操作系统: Ubuntu 22.04 LTS
公网IP: 3.106.191.40
私有IP: 172.31.30.184
密钥文件: ~/Downloads/trigo-key.pem
```

### SSH连接
```bash
# 标准SSH连接
ssh -i ~/Downloads/trigo-key.pem ubuntu@3.106.191.40

# 如果权限错误，修复密钥权限
chmod 400 ~/Downloads/trigo-key.pem
```

### 安全组端口配置
```
端口 22:   SSH（仅限你的IP）
端口 80:   HTTP（0.0.0.0/0 公开）
端口 443:  HTTPS（0.0.0.0/0 公开）
端口 5001: Flask应用（0.0.0.0/0 公开）- 可选，Nginx反向代理后可关闭
```

### 服务管理（systemd）
```bash
# 查看服务状态
sudo systemctl status trigo-nexus

# 启动服务
sudo systemctl start trigo-nexus

# 停止服务
sudo systemctl stop trigo-nexus

# 重启服务
sudo systemctl restart trigo-nexus

# 查看日志
sudo journalctl -u trigo-nexus -f

# 查看最近50条日志
sudo journalctl -u trigo-nexus -n 50
```

### 项目目录
```
路径: /home/ubuntu/Trigo-Nexus
虚拟环境: /home/ubuntu/Trigo-Nexus/venv
主程序: /home/ubuntu/Trigo-Nexus/app_v2.py
配置文件: /home/ubuntu/Trigo-Nexus/.env
```

### Nginx配置
```
配置文件: /etc/nginx/sites-available/trigonexus
启用链接: /etc/nginx/sites-enabled/trigonexus
日志: /var/log/nginx/access.log, /var/log/nginx/error.log

# Nginx命令
sudo nginx -t           # 测试配置
sudo systemctl reload nginx   # 重载配置
sudo systemctl restart nginx  # 重启服务
sudo systemctl status nginx   # 查看状态
```

### SSL证书（Let's Encrypt）
```
证书路径: /etc/letsencrypt/live/trigonexus.us/
自动续期: 已配置（cron每天运行certbot renew）

# 手动续期命令
sudo certbot renew --dry-run   # 测试续期
sudo certbot renew             # 实际续期
```

---

## 🌐 域名信息

### 域名注册商
```
提供商: Namecheap
域名: trigonexus.us
到期日期: [查看Namecheap账户]
管理URL: https://www.namecheap.com/myaccount/domain-list/
```

### DNS配置（Namecheap Advanced DNS）
```
类型    Host    值                  TTL
────────────────────────────────────────────────
A       @       3.106.191.40        Automatic
A       www     3.106.191.40        Automatic
TXT     @       google-site-verification=aUDcs29hGOPEg5vho03guvljHS5xJ3BQeSnMo_VF42w
TXT     @       v=spf1 include:spf.efwd.registrar-servers.com ~all
```

### 域名访问
```
主域名: https://trigonexus.us
www子域名: https://www.trigonexus.us
直接IP访问: http://3.106.191.40:5001（备用）
```

---

## 🔍 Google Search Console

### 账户信息
```
网站属性: trigonexus.us
验证方式: DNS TXT记录
验证码: google-site-verification=aUDcs29hGOPEg5vho03guvljHS5xJ3BQeSnMo_VF42w
管理URL: https://search.google.com/search-console
```

### Sitemap配置
```
Sitemap URL: https://trigonexus.us/sitemap.xml
提交状态: ✅ 成功
发现网页: 4个
- https://trigonexus.us/
- https://trigonexus.us/models
- https://trigonexus.us/models/qwen3-max
- https://trigonexus.us/models/deepseek-v3.2
```

### Robots.txt
```
URL: https://trigonexus.us/robots.txt
配置: 允许所有爬虫，禁止/api/和/socket.io/
```

---

## 🚀 快速部署命令

### 本地测试
```bash
cd /Users/sogmac/Desktop/Agent-Test/AI交易
python3 app_v2.py
# 访问: http://localhost:5001
```

### 提交代码到GitHub
```bash
cd /Users/sogmac/Desktop/Agent-Test/AI交易
git add .
git commit -m "更新说明"
git push
```

### 部署到AWS（完整流程）
```bash
# 1. 本地推送代码
git push

# 2. SSH到AWS
ssh -i ~/Downloads/trigo-key.pem ubuntu@3.106.191.40

# 3. 拉取最新代码
cd ~/Trigo-Nexus
git pull

# 4. 重启服务
sudo systemctl restart trigo-nexus

# 5. 验证服务状态
sudo systemctl status trigo-nexus

# 6. 查看日志（可选）
sudo journalctl -u trigo-nexus -f

# 7. 退出SSH
exit
```

### 一键部署脚本（在AWS上）
```bash
# 使用现有的部署脚本
ssh -i ~/Downloads/trigo-key.pem ubuntu@3.106.191.40 << 'EOF'
cd ~/Trigo-Nexus
git pull
sudo systemctl restart trigo-nexus
sudo systemctl status trigo-nexus --no-pager | head -20
EOF
```

---

## 📁 重要文件说明

### 核心代码文件
```
app_v2.py              - Flask主应用（生产版本）
ai_trader_v2.py        - AI交易逻辑
config.py              - 配置文件（包含API密钥）
leverage_engine.py     - 杠杆交易引擎
market_data.py         - 市场数据获取
technical_indicators.py - 技术指标计算
kline_data.py          - K线数据管理
order_manager.py       - 订单管理
trading_engine.py      - 交易引擎
```

### 配置文件
```
requirements.txt       - Python依赖包
deploy_aws.sh         - AWS自动化部署脚本
.env                  - 环境变量（在AWS上，不在Git中）
```

### 前端文件
```
templates/index.html           - 首页
templates/model_detail.html    - 模型详情页
static/css/style.css          - 样式表
static/js/app.js              - 前端JavaScript
static/favicon.svg            - 网站图标
static/sitemap.xml            - 网站地图
static/robots.txt             - 爬虫规则
```

### 文档文件
```
IMPORTANT.md           - 本文件（重要信息汇总）
README.md             - 项目说明
Google搜索收录指南.md  - SEO配置指南
生成Favicon图标.md    - 图标制作指南
```

---

## 🆘 紧急恢复指南

### 场景1：网站无法访问

#### 诊断步骤：
```bash
# 1. 检查AWS服务器是否运行
ssh -i ~/Downloads/trigo-key.pem ubuntu@3.106.191.40

# 2. 检查服务状态
sudo systemctl status trigo-nexus

# 3. 检查Nginx状态
sudo systemctl status nginx

# 4. 查看错误日志
sudo journalctl -u trigo-nexus -n 50
sudo tail -50 /var/log/nginx/error.log
```

#### 修复方法：
```bash
# 重启应用服务
sudo systemctl restart trigo-nexus

# 重启Nginx
sudo systemctl restart nginx

# 如果端口被占用
sudo lsof -i :5001
sudo kill -9 [PID]
```

---

### 场景2：代码部署失败

#### 诊断步骤：
```bash
# 1. SSH到服务器
ssh -i ~/Downloads/trigo-key.pem ubuntu@3.106.191.40

# 2. 检查Git状态
cd ~/Trigo-Nexus
git status

# 3. 查看最近的日志
sudo journalctl -u trigo-nexus -n 100
```

#### 修复方法：
```bash
# 如果有未提交的更改
git reset --hard HEAD
git pull

# 如果依赖有问题
source venv/bin/activate
pip install -r requirements.txt

# 重启服务
sudo systemctl restart trigo-nexus
```

---

### 场景3：SSL证书过期

#### 检查证书：
```bash
sudo certbot certificates
```

#### 续期证书：
```bash
sudo certbot renew
sudo systemctl reload nginx
```

---

### 场景4：数据库/价格获取失败

#### 检查API限制：
```bash
# Finnhub API限制：60次/分钟
# Binance API：公开端点，无限制

# 查看日志中的API错误
sudo journalctl -u trigo-nexus -f | grep -i "error\|timeout"
```

#### 修复方法：
- 如果Finnhub超限：等待1分钟后重试
- 如果Binance失败：代码会自动切换备用端点
- 检查网络连接：`ping api.binance.com`

---

### 场景5：完全重新部署

如果一切都失败，从头开始：

```bash
# 1. SSH到服务器
ssh -i ~/Downloads/trigo-key.pem ubuntu@3.106.191.40

# 2. 停止服务
sudo systemctl stop trigo-nexus

# 3. 备份当前代码
mv ~/Trigo-Nexus ~/Trigo-Nexus.backup

# 4. 重新克隆仓库
git clone https://github.com/Jackietomtam/Trigo-Nexus.git
cd Trigo-Nexus

# 5. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 6. 安装依赖
pip install -r requirements.txt

# 7. 创建.env文件
cat > .env << 'EOF'
OPENROUTER_API_KEY=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
DASHSCOPE_API_KEY=sk-79529efd5f434d8aa9eea08c17441096
DASHSCOPE_DEEPSEEK_API_KEY=sk-f4168a5a023345afb1ce334f25b77365
FINNHUB_API_KEY=d1ivl31r01qhbuvsiufgd1ivl31r01qhbuvsiug0
FLASK_ENV=production
PORT=5001
EOF

# 8. 启动服务
sudo systemctl start trigo-nexus
sudo systemctl status trigo-nexus
```

---

## 📊 监控与性能

### 服务器资源监控
```bash
# CPU和内存使用
htop

# 磁盘使用
df -h

# 查看进程
ps aux | grep python

# 网络连接
netstat -tulpn | grep 5001
```

### 应用性能
```bash
# 查看实时日志
sudo journalctl -u trigo-nexus -f

# 查看错误
sudo journalctl -u trigo-nexus | grep -i error

# 统计请求数
sudo tail -1000 /var/log/nginx/access.log | wc -l
```

---

## 📞 联系方式与资源

### 云服务提供商
- **AWS控制台**: https://console.aws.amazon.com/
- **Namecheap**: https://www.namecheap.com/

### API文档
- **OpenRouter**: https://openrouter.ai/docs
- **阿里云百炼**: https://help.aliyun.com/zh/dashscope
- **Finnhub**: https://finnhub.io/docs/api
- **Binance**: https://binance-docs.github.io/apidocs/spot/en/

### 工具
- **SSL检查**: https://www.ssllabs.com/ssltest/
- **DNS检查**: https://dnschecker.org/
- **网站速度测试**: https://pagespeed.web.dev/
- **Favicon生成**: https://favicon.io/

---

## ⚠️ 安全提醒

1. **永远不要**将此文件提交到公开仓库
2. **定期更换** API密钥（建议每3-6个月）
3. **备份**重要数据和配置
4. **监控** AWS账单，避免意外费用
5. **更新**系统和依赖包，保持安全

### 添加到.gitignore
确保以下内容在`.gitignore`中：
```
.env
IMPORTANT.md
*.pem
__pycache__/
*.pyc
.DS_Store
```

---

## 🔄 定期维护任务

### 每周
- [ ] 检查服务运行状态
- [ ] 查看错误日志
- [ ] 监控AWS账单

### 每月
- [ ] 检查SSL证书有效期
- [ ] 更新系统包：`sudo apt update && sudo apt upgrade`
- [ ] 审查API使用量

### 每季度
- [ ] 考虑更换API密钥
- [ ] 备份重要配置
- [ ] 审查安全组规则

---

**最后更新**: 2025-10-26
**版本**: 1.0
**维护**: Jackietomtam

---

🎉 **恭喜！你的Trigo Nexus AI交易平台已完全部署并运行中！**

**访问地址**: https://trigonexus.us

