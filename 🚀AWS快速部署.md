# 🚀 AWS 快速部署 - 5分钟完成

## 📋 你需要的东西
- ✅ AWS 账号（已准备好）
- ✅ 5 分钟时间
- ✅ SSH 客户端（Mac/Linux 自带，Windows 用 PuTTY）

---

## 🎯 三步完成部署

### 步骤 1: 启动 EC2 实例（2 分钟）

1. 登录 AWS 控制台: https://console.aws.amazon.com/
2. 搜索 **EC2** → 点击 **"启动实例"**
3. 填写配置：
   ```
   名称: Trigo-Nexus
   AMI: Ubuntu Server 22.04 LTS
   实例类型: t2.micro（免费）
   密钥对: 新建并下载 trigo-nexus-key.pem
   ```
4. **网络设置** → 添加规则：
   - SSH (22)
   - HTTP (80)  
   - 自定义 TCP (5001) ← 重要！
5. 点击 **"启动实例"**

---

### 步骤 2: 连接到实例（1 分钟）

```bash
# Mac/Linux
chmod 400 ~/Downloads/trigo-nexus-key.pem
ssh -i ~/Downloads/trigo-nexus-key.pem ubuntu@你的EC2公网IP
```

**找到你的公网IP：**
EC2 控制台 → 点击实例 → 查看 "公有 IPv4 地址"

---

### 步骤 3: 一键部署（3 分钟）

连接成功后，复制粘贴以下命令：

```bash
curl -O https://raw.githubusercontent.com/Jackietomtam/Trigo-Nexus/main/deploy_aws.sh && chmod +x deploy_aws.sh && ./deploy_aws.sh
```

**就这么简单！** 🎉

脚本会自动：
- ✅ 安装所有依赖
- ✅ 下载代码
- ✅ 配置服务
- ✅ 启动应用

---

## 🌐 访问你的应用

部署完成后，在浏览器打开：
```
http://你的EC2公网IP:5001/
```

例如：`http://52.23.45.67:5001/`

---

## 📊 常用命令

```bash
# 查看服务状态
sudo systemctl status trigo-nexus

# 查看实时日志
sudo journalctl -u trigo-nexus -f

# 重启服务
sudo systemctl restart trigo-nexus
```

---

## 💰 费用

**免费套餐（首年）：**
- t2.micro 实例: 750 小时/月（免费）
- 足够 24/7 运行
- **完全免费第一年！**

---

## 🎊 完成！

现在你的 AI 交易系统：
- ✅ 在 AWS 上 24/7 运行
- ✅ 使用真实 Binance 数据（无封锁）
- ✅ 使用 Finnhub 备用数据源
- ✅ 自动重启保护
- ✅ 公网可访问

**需要详细指南？** 查看 `AWS部署指南.md`

---

## 🔥 下一步（可选）

1. **配置域名**（如 trade.yourdomain.com）
2. **启用 HTTPS**（Let's Encrypt 免费）
3. **设置监控**（CloudWatch）
4. **自动备份**

详见 `AWS部署指南.md` 📚

---

## ❓ 遇到问题？

**无法访问 5001 端口？**
→ 检查安全组是否添加了端口 5001 规则

**服务无法启动？**
→ 查看日志：`sudo journalctl -u trigo-nexus -xe`

**其他问题？**
→ 查看完整文档：`AWS部署指南.md`

---

**祝你交易顺利！** 🚀📈

