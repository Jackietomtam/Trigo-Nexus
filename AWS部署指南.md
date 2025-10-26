# 🚀 AWS EC2 部署指南 - Trigo Nexus

## 📋 前提条件

✅ AWS 账号已准备好  
✅ 已获得 AWS Access Key（可选）  
✅ 项目已推送到 GitHub: `Jackietomtam/Trigo-Nexus`

---

## 🎯 快速部署（3 步完成）

### 步骤 1️⃣: 启动 EC2 实例

#### 1.1 登录 AWS 控制台
- 访问：https://console.aws.amazon.com/
- 搜索并进入 **EC2** 服务

#### 1.2 启动实例
点击 **"Launch Instance"** (启动实例)

#### 1.3 配置实例
```
名称: Trigo-Nexus-Trading

AMI (操作系统):
  推荐: Ubuntu Server 22.04 LTS (Free tier eligible)
  或:   Amazon Linux 2023

实例类型:
  推荐: t2.micro (免费套餐)
  或:   t3.micro (更好的性能)

密钥对 (Key pair):
  - 新建密钥对: trigo-nexus-key
  - 类型: RSA
  - 格式: .pem (Mac/Linux) 或 .ppk (Windows)
  - 下载并保存好（无法重新下载）

网络设置:
  ✅ 允许来自互联网的 SSH 流量
  ✅ 允许来自互联网的 HTTPS 流量
  ✅ 允许来自互联网的 HTTP 流量

存储:
  8-20 GB gp3 (足够)

高级详细信息:
  - 其他保持默认即可
```

#### 1.4 添加安全组规则
在 **"网络设置"** 中，点击 **"编辑"**，添加规则：

| 类型 | 协议 | 端口范围 | 源 | 说明 |
|-----|------|---------|-----|-----|
| SSH | TCP | 22 | 0.0.0.0/0 | SSH 访问 |
| HTTP | TCP | 80 | 0.0.0.0/0 | HTTP（可选） |
| 自定义 TCP | TCP | 5001 | 0.0.0.0/0 | Flask 应用 |

#### 1.5 启动实例
- 检查配置无误
- 点击 **"启动实例"**
- 等待实例状态变为 **"Running"** (约 1-2 分钟)

---

### 步骤 2️⃣: 连接到 EC2 实例

#### 2.1 获取公网 IP
在 EC2 控制台，找到你的实例，记下：
- **公有 IPv4 地址** (例如: 52.23.45.67)

#### 2.2 连接到实例

**Mac/Linux 用户：**
```bash
# 1. 设置密钥权限
chmod 400 ~/Downloads/trigo-nexus-key.pem

# 2. SSH 连接
ssh -i ~/Downloads/trigo-nexus-key.pem ubuntu@你的公网IP

# 例如:
# ssh -i ~/Downloads/trigo-nexus-key.pem ubuntu@52.23.45.67
```

**Windows 用户（使用 PuTTY）：**
1. 下载并安装 PuTTY
2. 使用 PuTTYgen 转换 .pem 为 .ppk
3. 在 PuTTY 中配置：
   - Host: ubuntu@你的公网IP
   - Port: 22
   - Auth: 加载 .ppk 密钥文件

---

### 步骤 3️⃣: 一键部署

连接成功后，运行以下命令：

```bash
# 1. 下载部署脚本
curl -O https://raw.githubusercontent.com/Jackietomtam/Trigo-Nexus/main/deploy_aws.sh

# 2. 添加执行权限
chmod +x deploy_aws.sh

# 3. 运行部署脚本（自动安装所有依赖）
./deploy_aws.sh
```

**部署过程约 3-5 分钟**，脚本会自动：
1. ✅ 更新系统
2. ✅ 安装 Python 3.10
3. ✅ 克隆 GitHub 代码
4. ✅ 安装所有依赖
5. ✅ 配置环境变量
6. ✅ 创建系统服务（自动启动）
7. ✅ 配置防火墙
8. ✅ 启动应用

---

## 🎉 部署完成！

### 访问你的应用

部署完成后，你会看到访问地址：
```
🌐 访问地址:
  http://你的公网IP:5001/
```

在浏览器中打开这个地址，你就能看到 **Trigo Nexus AI Trading System** 了！

---

## 📊 管理命令

### 查看服务状态
```bash
sudo systemctl status trigo-nexus
```

### 查看实时日志
```bash
sudo journalctl -u trigo-nexus -f
```

### 重启服务
```bash
sudo systemctl restart trigo-nexus
```

### 停止服务
```bash
sudo systemctl stop trigo-nexus
```

### 启动服务
```bash
sudo systemctl start trigo-nexus
```

---

## 🔄 更新代码

当你更新 GitHub 代码后，在 EC2 上运行：
```bash
cd ~/Trigo-Nexus
git pull
sudo systemctl restart trigo-nexus
```

---

## 🌐 配置域名（可选）

如果你有域名，可以：

### 1. 使用 AWS Route 53
- 创建托管区域
- 添加 A 记录指向你的 EC2 公网 IP

### 2. 或使用其他 DNS 服务
- Cloudflare
- Namecheap
- GoDaddy

配置 A 记录：
```
Type: A
Name: trade (或 @)
Value: 你的EC2公网IP
TTL: 300
```

---

## 🔒 安全加固（推荐）

### 1. 限制 SSH 访问
编辑安全组，将 SSH (端口 22) 的源改为 **"我的 IP"**

### 2. 设置 HTTPS（推荐）
```bash
# 安装 Nginx + Let's Encrypt
sudo apt-get install -y nginx certbot python3-certbot-nginx

# 配置反向代理
sudo nano /etc/nginx/sites-available/trigo-nexus

# 添加配置:
server {
    listen 80;
    server_name 你的域名.com;

    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# 启用配置
sudo ln -s /etc/nginx/sites-available/trigo-nexus /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# 申请 SSL 证书
sudo certbot --nginx -d 你的域名.com
```

### 3. 定期备份
```bash
# 创建备份脚本
sudo nano /usr/local/bin/backup-trigo.sh

# 添加:
#!/bin/bash
tar -czf ~/backups/trigo-nexus-$(date +%Y%m%d).tar.gz ~/Trigo-Nexus
```

---

## 💰 成本估算

### Free Tier (首年免费)
- t2.micro: 750 小时/月（足够 24/7 运行）
- 存储: 30 GB
- 流量: 15 GB/月出站

### 超出免费套餐后
- t2.micro: ~$8.5/月
- t3.micro: ~$7.5/月（性能更好）
- 存储: ~$0.1/GB/月
- 流量: ~$0.09/GB

---

## ❓ 常见问题

### Q: 无法访问 5001 端口？
**A:** 检查安全组规则是否添加了端口 5001

### Q: 服务无法启动？
**A:** 查看日志：`sudo journalctl -u trigo-nexus -xe`

### Q: Binance API 仍然报错？
**A:** AWS EC2 的 IP 不会被封锁，如果还有问题，检查 API 密钥

### Q: 如何更改端口？
**A:** 编辑 `.env` 文件中的 `PORT=5001`，然后重启服务

### Q: 想要更高性能？
**A:** 升级到 t3.small 或 t3.medium

---

## 📞 需要帮助？

如果部署过程中遇到问题：
1. 查看日志：`sudo journalctl -u trigo-nexus -f`
2. 检查服务状态：`sudo systemctl status trigo-nexus`
3. 检查防火墙：`sudo ufw status`

---

## 🎊 完成！

现在你的 AI 交易系统已经：
- ✅ 部署在 AWS EC2 上
- ✅ 使用真实的 Binance 数据（不会被封锁）
- ✅ 24/7 稳定运行
- ✅ 自动重启（如果崩溃）
- ✅ 可通过公网访问

享受你的 Trigo Nexus AI Trading System！🚀

