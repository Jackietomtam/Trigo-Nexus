# 🚀 AWS 快速部署指南

## 最快部署（3步骤）

### 1️⃣ 准备 EC2 实例
```bash
# AWS Console:
# - Ubuntu 22.04 LTS
# - t3.medium (2vCPU, 4GB RAM) 或更高
# - 安全组：开放 80, 443 端口
# - SSH 登录实例
```

### 2️⃣ 上传代码并运行部署脚本
```bash
# 方式A：如果代码在 Git 仓库
ssh ubuntu@<EC2_IP>
cd /opt
sudo git clone YOUR_REPO_URL ai-trader
cd ai-trader
bash deploy.sh

# 方式B：从本地上传
# 本地执行：
scp -r -i your-key.pem /Users/sogmac/Desktop/Agent-Test/AI交易 ubuntu@<EC2_IP>:/tmp/
# 远程执行：
ssh ubuntu@<EC2_IP>
sudo mv /tmp/AI交易 /opt/ai-trader
sudo chown -R ubuntu:ubuntu /opt/ai-trader
cd /opt/ai-trader
bash deploy.sh
```

### 3️⃣ 配置 API Keys 并启动
```bash
# 编辑环境变量
nano /opt/ai-trader/.env
# 填入你的 API Keys（参考 env.template）

# 启动服务
sudo systemctl start ai-trader

# 查看状态
sudo systemctl status ai-trader

# 查看日志（确保没有错误）
sudo journalctl -u ai-trader -f
```

### ✅ 完成！访问应用
```
http://<EC2_PUBLIC_IP>/edition1
http://<EC2_PUBLIC_IP>/edition2  
http://<EC2_PUBLIC_IP>/models
```

---

## 常用命令

### 服务管理
```bash
# 启动
sudo systemctl start ai-trader

# 停止
sudo systemctl stop ai-trader

# 重启
sudo systemctl restart ai-trader

# 查看状态
sudo systemctl status ai-trader

# 查看日志
sudo journalctl -u ai-trader -f
```

### 代码更新
```bash
cd /opt/ai-trader
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart ai-trader
```

### 排查问题
```bash
# 应用日志
tail -f /var/log/ai-trader/error.log
tail -f /var/log/ai-trader/access.log

# Nginx 日志
sudo tail -f /var/log/nginx/ai-trader-error.log

# 手动测试运行
cd /opt/ai-trader
source venv/bin/activate
export $(cat .env | xargs)
python app_dual_edition.py
```

---

## 可选：配置 HTTPS

```bash
# 1. 将域名 DNS A 记录指向 EC2 公网 IP
# 2. 运行 certbot
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# 证书会自动续期，测试一下
sudo certbot renew --dry-run
```

---

## 详细文档

- 完整部署指南：见 `AWS_DEPLOY.md`
- 环境变量模板：见 `env.template`
- 应用配置：见 `config.py`

---

## 获取 API Keys

1. **Finnhub API** (市场数据)
   - 注册：https://finnhub.io/register
   - 免费套餐：60 calls/min
   
2. **阿里云 DashScope** (Qwen/DeepSeek 模型)
   - 注册：https://dashscope.aliyun.com/
   - 开通模型：qwen-plus, deepseek-v3.2-exp
   - 获取 API Key

---

**需要帮助？** 查看日志文件或提交 Issue





