# 🚀 立即部署 Available Cash 修复

## 📋 修复内容摘要

已修复的关键问题：
1. ✅ **Available Cash 显示为 $0.00** - 添加了非负数保护
2. ✅ **持仓 Quantity 显示为 0.0000** - 提升到 6 位小数精度
3. ✅ **图表变成直线** - 防止产生尘埃仓位（添加 $50 最小名义金额阈值）
4. ✅ **Edition 2 相同问题** - 统一修复 Edition 1 和 Edition 2

## 🔧 部署步骤

### 步骤 1: SSH 登录服务器
```bash
ssh -i ~/Downloads/trigo-key.pem ubuntu@3.106.191.40
```

### 步骤 2: 进入项目目录并拉取最新代码
```bash
cd /home/ubuntu/AI交易

# 查看当前状态
git status

# 拉取最新修复
git pull origin main
```

**如果提示有本地修改冲突：**
```bash
# 备份本地修改
git stash

# 拉取最新代码
git pull origin main

# 如果需要恢复本地修改
git stash pop
```

### 步骤 3: 检查修复的文件
```bash
# 查看最近的提交
git log --oneline -5

# 确认以下文件已更新
ls -lh leverage_engine.py ai_trader_v2.py app_dual_edition.py ai_trader_edition2_new.py
```

### 步骤 4: 重启服务
```bash
# 重启 Trigo Nexus 服务
sudo systemctl restart trigo-ai-trader

# 等待 3 秒
sleep 3

# 检查服务状态
sudo systemctl status trigo-ai-trader
```

**预期输出：**
```
● trigo-ai-trader.service - Trigo Nexus AI Trading System
   Loaded: loaded (/etc/systemd/system/trigo-ai-trader.service; enabled)
   Active: active (running) since ...
```

### 步骤 5: 实时监控日志
```bash
# 实时查看服务日志（Ctrl+C 退出）
sudo journalctl -u trigo-ai-trader -f
```

**应该看到的关键日志：**
```
🚀 Edition 1 系统启动...
🚀 Edition 2 系统启动（带新闻功能）...
✓ Edition 1: 已初始化 2 个AI交易员
✓ Edition 2: 已初始化 2 个AI交易员（带新闻功能）
```

**修复生效的标志：**
```
⚠ [E1] QWEN3 MAX 跳过开多 BTC: 名义金额不足（$15.23<$50.00）
  ← 这说明最小名义金额阈值已生效！

→ [E1] QWEN3 MAX 账户: $99,278.25, 持仓数: 4
  ← Available Cash 不再为 0
```

**如果看到错误日志：**
```bash
# 查看最近 100 行错误日志
sudo journalctl -u trigo-ai-trader -n 100 --no-pager | grep -i error

# 查看完整启动日志
sudo journalctl -u trigo-ai-trader -b -n 200
```

### 步骤 6: 验证前端显示

打开浏览器访问以下页面：

1. **Edition 1**: http://3.106.191.40:5001/edition1
2. **Edition 2**: http://3.106.191.40:5001/edition2

**检查项目：**
- [ ] 左下角 "Available Cash" 不再显示为 $0.00
- [ ] 点击 AI 卡片查看持仓，Quantity 显示非零值（如 0.000143）
- [ ] 图表随时间波动（不是水平直线）
- [ ] 查看"对话"标签，确认 AI 的 Available Cash 数值正常

### 步骤 7: 检查数据库/持仓状态

```bash
# 如果使用了持久化存储，检查持仓文件
cd /home/ubuntu/AI交易
ls -lh *.json 2>/dev/null || echo "无持久化文件"

# 查看当前 Python 进程
ps aux | grep python | grep -v grep
```

## 🔍 故障排查

### 问题 1: 服务启动失败
```bash
# 查看详细错误
sudo journalctl -u trigo-ai-trader -xe

# 常见原因：
# - 端口 5001 被占用
# - Python 依赖缺失
# - 配置文件错误

# 手动测试启动
cd /home/ubuntu/AI交易
python3 app_dual_edition.py
```

### 问题 2: Git pull 冲突
```bash
# 查看冲突文件
git status

# 方案 A: 强制使用远程版本（丢弃本地修改）
git fetch origin
git reset --hard origin/main

# 方案 B: 手动解决冲突
git merge --abort
git stash
git pull
```

### 问题 3: 服务运行但仍显示 $0.00
```bash
# 1. 确认代码已更新
grep -n "available_cash = 0.0" /home/ubuntu/AI交易/leverage_engine.py
# 应该能找到修复代码（第 325 行左右）

# 2. 确认服务使用的是最新代码
sudo systemctl restart trigo-ai-trader
sleep 5
sudo journalctl -u trigo-ai-trader -n 50 | grep "初始化"

# 3. 清除浏览器缓存
# 按 Ctrl+Shift+R 强制刷新前端
```

### 问题 4: 持仓仍显示 0.0000
```bash
# 检查持仓精度修复
grep "round(pos.get('quantity'" /home/ubuntu/AI交易/ai_trader_v2.py
# 应该看到 round(..., 6) 而非 round(..., 2)

# 重启后需要等待新的交易产生新持仓
# 旧持仓可能仍显示 2 位精度（这是正常的）
```

## 📊 验证清单

完成以下验证后，修复即算成功：

### 后端验证
- [ ] `git log` 显示最新提交包含修复
- [ ] 服务状态为 `active (running)`
- [ ] 日志中看到 "跳过开多: 名义金额不足" 消息
- [ ] 没有 Python 错误或异常

### 前端验证（Edition 1）
- [ ] Available Cash 显示非零金额（如 $23,485.32）
- [ ] 持仓 Quantity 显示 6 位小数（如 0.000143）
- [ ] 图表曲线随市场波动
- [ ] AI 对话中的 Available Cash 数值合理

### 前端验证（Edition 2）
- [ ] 同 Edition 1 的所有验证项
- [ ] 对话中包含新闻数据
- [ ] 新闻标签正常显示

## 🎯 预期改进

修复后，系统将展现：

| 指标 | 修复前 | 修复后 |
|------|--------|--------|
| Available Cash | $0.00 ❌ | $23,485.32 ✅ |
| 持仓 Quantity | 0.0000 ❌ | 0.000143 ✅ |
| 图表 | 水平直线 ❌ | 波动曲线 ✅ |
| 尘埃仓位 | 大量产生 ❌ | 不再产生 ✅ |
| AI 决策 | 基于错误数据 ❌ | 基于准确数据 ✅ |

## 🆘 需要帮助？

如果遇到问题，提供以下信息：

```bash
# 收集诊断信息
echo "=== Git Status ===" > /tmp/debug.log
git log --oneline -3 >> /tmp/debug.log
echo "=== Service Status ===" >> /tmp/debug.log
sudo systemctl status trigo-ai-trader >> /tmp/debug.log
echo "=== Recent Logs ===" >> /tmp/debug.log
sudo journalctl -u trigo-ai-trader -n 100 >> /tmp/debug.log
echo "=== Process ===" >> /tmp/debug.log
ps aux | grep python >> /tmp/debug.log

# 查看诊断文件
cat /tmp/debug.log
```

---

**部署时间**: 预计 5-10 分钟  
**风险等级**: 低（纯 bug 修复，不改变业务逻辑）  
**回滚方案**: `git reset --hard HEAD~1 && sudo systemctl restart trigo-ai-trader`

