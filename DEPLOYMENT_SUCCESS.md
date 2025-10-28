# 🎉 AWS 部署成功！

## ✅ 部署状态

**服务器**: 3.106.191.40  
**状态**: ✅ 运行中  
**部署时间**: 2025-10-26 17:07 UTC

---

## 🌐 访问地址

### 主要页面
- **Edition 1 (基础版)**: http://3.106.191.40/edition1
- **Edition 2 (新闻增强版)**: http://3.106.191.40/edition2
- **模型对比**: http://3.106.191.40/models
- **首页**: http://3.106.191.40/

### 直接访问（无 Nginx）
- http://3.106.191.40:5001/edition2

---

## ⚙️ 服务管理命令

### 查看服务状态
```bash
ssh -i ~/Downloads/trigo-key.pem ubuntu@3.106.191.40 'sudo systemctl status ai-trader'
```

### 重启服务
```bash
ssh -i ~/Downloads/trigo-key.pem ubuntu@3.106.191.40 'sudo systemctl restart ai-trader'
```

### 查看实时日志
```bash
ssh -i ~/Downloads/trigo-key.pem ubuntu@3.106.191.40 'sudo journalctl -u ai-trader -f'
```

### 停止服务
```bash
ssh -i ~/Downloads/trigo-key.pem ubuntu@3.106.191.40 'sudo systemctl stop ai-trader'
```

---

## 📊 系统配置

### 已安装组件
- ✅ Python 3.10
- ✅ Flask + SocketIO
- ✅ Gunicorn (eventlet worker)
- ✅ Nginx 反向代理
- ✅ Systemd 服务（开机自启动）

### API Keys 配置
所有 API keys 已配置在 `/opt/ai-trader/.env`:
- ✅ FINNHUB_API_KEY
- ✅ DASHSCOPE_API_KEY (Qwen)
- ✅ DASHSCOPE_DEEPSEEK_API_KEY (DeepSeek)

---

## 🔧 常见操作

### 更新代码
```bash
cd /Users/sogmac/Desktop/Agent-Test/AI交易
rsync -avz --exclude='venv*' --exclude='*.pyc' --exclude='__pycache__' --exclude='.git' --exclude='*.log' -e 'ssh -i ~/Downloads/trigo-key.pem' . ubuntu@3.106.191.40:/opt/ai-trader/
ssh -i ~/Downloads/trigo-key.pem ubuntu@3.106.191.40 'sudo systemctl restart ai-trader'
```

### 修改配置文件
```bash
ssh -i ~/Downloads/trigo-key.pem ubuntu@3.106.191.40
nano /opt/ai-trader/.env
# 修改后保存并重启
sudo systemctl restart ai-trader
```

### 查看 Nginx 日志
```bash
ssh -i ~/Downloads/trigo-key.pem ubuntu@3.106.191.40 'sudo tail -f /var/log/nginx/ai-trader-access.log'
ssh -i ~/Downloads/trigo-key.pem ubuntu@3.106.191.40 'sudo tail -f /var/log/nginx/ai-trader-error.log'
```

---

## 🔒 安全提醒

1. **端口检查**: 确保 AWS 安全组已开放 80 端口（HTTP）
2. **HTTPS**: 建议配置 SSL 证书（使用 certbot）
3. **SSH**: 建议限制 SSH 访问仅允许特定 IP
4. **密钥保护**: 保管好 `trigo-key.pem`

---

## 🚀 下一步（可选）

### 配置 HTTPS
```bash
ssh -i ~/Downloads/trigo-key.pem ubuntu@3.106.191.40
sudo certbot --nginx -d yourdomain.com
```

### 配置域名
1. 在域名 DNS 设置中添加 A 记录：
   ```
   @ (或 www) → 3.106.191.40
   ```
2. 更新 Nginx 配置：
   ```bash
   sudo nano /etc/nginx/sites-available/ai-trader
   # 修改 server_name _ 为你的域名
   sudo systemctl restart nginx
   ```

### 监控和日志
- 考虑安装 htop 或 glances 监控资源
- 设置日志轮转防止磁盘占满
- 可选：配置 CloudWatch 监控

---

## 📞 故障排查

### 服务无法启动
```bash
# 查看详细错误
ssh -i ~/Downloads/trigo-key.pem ubuntu@3.106.191.40 'sudo journalctl -u ai-trader -n 100'

# 检查端口占用
ssh -i ~/Downloads/trigo-key.pem ubuntu@3.106.191.40 'sudo lsof -i:5001'

# 手动测试
ssh -i ~/Downloads/trigo-key.pem ubuntu@3.106.191.40
cd /opt/ai-trader
source venv/bin/activate
export $(cat .env | xargs)
python app_dual_edition.py
```

### 页面无法访问
1. 检查 AWS 安全组是否开放 80 端口
2. 检查 Nginx 状态：`sudo systemctl status nginx`
3. 检查防火墙：`sudo ufw status`

---

## ✅ 部署清单

- [x] EC2 实例配置
- [x] 系统依赖安装
- [x] Python 环境设置
- [x] 代码上传
- [x] API Keys 配置
- [x] Systemd 服务配置
- [x] Nginx 反向代理配置
- [x] 服务启动成功
- [x] 应用响应正常

---

**部署完成！你的 AI 交易平台已经在 AWS 上运行了！** 🎊

访问 http://3.106.191.40/edition2 开始体验！



