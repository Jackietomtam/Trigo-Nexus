# 🎯 Trigo Nexus - Edition 1 & 2 双版本升级指南

## ✅ 完成的工作

### 1. 创建了双版本系统架构
- ✅ Edition 1: 原版AI交易系统
- ✅ Edition 2: 增强版（集成新闻和市场情绪）

### 2. 新文件列表

| 文件 | 用途 |
|------|------|
| `ai_trader_edition2.py` | Edition 2 AI交易员（带新闻功能） |
| `app_dual_edition.py` | 双版本Flask应用 |
| `templates/edition1.html` | Edition 1 前端页面 |
| `templates/edition2.html` | Edition 2 前端页面 |
| `crypto_news.py` | 新闻API封装（已存在） |
| `start_dual_edition.sh` | 快速启动脚本 |

### 3. 关键特性

#### Edition 1（原版）
- ✅ 使用AITraderV2
- ✅ 基于技术指标决策
- ✅ 独立的市场数据和引擎
- ✅ 路由前缀：`/edition1`

#### Edition 2（增强版）
- ✅ 使用AITraderEdition2
- ✅ 集成过去3分钟的新闻（如果有）
- ✅ 集成Fear & Greed Index（恐慌贪婪指数）
- ✅ 集成市场情绪分析
- ✅ 独立的市场数据和引擎
- ✅ 路由前缀：`/edition2`

---

## 🔒 数据隔离保障

### 1. 独立的系统实例

```python
# Edition 1 专用实例
market_data_e1 = MarketData()
kline_data_e1 = KLineData(market_data_e1)
leverage_engine_e1 = LeverageEngine(INITIAL_BALANCE)
order_manager_e1 = OrderManager(leverage_engine_e1)
ai_traders_e1 = []

# Edition 2 专用实例
market_data_e2 = MarketData()
kline_data_e2 = KLineData(market_data_e2)
leverage_engine_e2 = LeverageEngine(INITIAL_BALANCE)
order_manager_e2 = OrderManager(leverage_engine_e2)
ai_traders_e2 = []
```

### 2. 独立的交易循环

- Edition 1 和 Edition 2 各自运行在独立的线程中
- 互不干扰，完全隔离
- 各自有独立的状态跟踪

### 3. 独立的API路由

#### Edition 1 路由
```
GET  /edition1                  # 页面
GET  /api/edition1/prices       # 价格
GET  /api/edition1/leaderboard  # 排行榜
GET  /api/edition1/trades       # 交易记录
GET  /api/edition1/chat         # AI对话
GET  /api/edition1/history      # 历史数据
```

#### Edition 2 路由
```
GET  /edition2                  # 页面
GET  /api/edition2/prices       # 价格
GET  /api/edition2/leaderboard  # 排行榜
GET  /api/edition2/trades       # 交易记录
GET  /api/edition2/chat         # AI对话
GET  /api/edition2/history      # 历史数据
GET  /api/edition2/news         # 新闻（Edition 2专有）
GET  /api/edition2/market-sentiment  # 市场情绪（Edition 2专有）
```

---

## 📰 Edition 2 新增功能详解

### 1. Fear & Greed Index（恐慌贪婪指数）

```python
{
    'value': 40,                    # 0-100
    'classification': 'Fear',        # Extreme Fear / Fear / Neutral / Greed / Extreme Greed
    'timestamp': '2025-10-26 08:00'
}
```

**AI如何使用**：
- 0-25: 极度恐慌 → 可能是买入机会
- 26-45: 恐慌 → 市场谨慎
- 46-55: 中性
- 56-75: 贪婪 → 注意风险
- 76-100: 极度贪婪 → 可能是卖出信号

### 2. 过去3分钟新闻

```python
# 只有当过去3分钟内有新闻时才包含
📰 过去3分钟内的新闻 (2条):

1. [2025-10-26 15:30] Cardano ETF Optimism Persists Amid SEC Silence
   来源: coinotag | 相关: BTC, ADA

2. [2025-10-26 15:28] Bitcoin Miner Accumulation Signals Market Strength
   来源: ambcrypto | 相关: BTC
```

**特点**：
- ✅ 只在有新闻时才包含（不会干扰AI）
- ✅ 3分钟缓存（避免频繁请求）
- ✅ 自动标注相关币种
- ✅ 提示AI根据新闻调整策略

### 3. 市场情绪分析

```python
[新闻情绪分析] 💭
  - 总体情绪: NEUTRAL
  - 情绪分数: 0.2 (-1到1之间)
  - 正面新闻: 30%
  - 负面新闻: 15%
  - 中性新闻: 55%
  - 分析样本: 20条
```

**计算方法**：
- 分析最近20条新闻的关键词
- 正面关键词：bullish, surge, rally, adoption...
- 负面关键词：bearish, crash, regulation, ban...
- 情绪分数 = (正面 - 负面) / 总数

---

## 🚀 本地测试

### 方法1：使用启动脚本（推荐）

```bash
cd '/Users/sogmac/Desktop/Agent-Test/AI交易'
./start_dual_edition.sh
```

### 方法2：直接启动

```bash
cd '/Users/sogmac/Desktop/Agent-Test/AI交易'
source venv_local/bin/activate
python app_dual_edition.py
```

### 访问地址

- **Edition 1**: http://localhost:5001/edition1
- **Edition 2**: http://localhost:5001/edition2

---

## 🔄 从原版切换到双版本

### 在本地测试
1. 停止原版 app_v2.py（如果在运行）
2. 启动 app_dual_edition.py
3. 访问 http://localhost:5001/edition1 或 /edition2

### 在AWS部署
1. SSH到服务器
2. 备份当前代码
3. 上传新文件
4. 修改systemd服务
5. 重启服务

---

## 📊 导航栏变化

### 原版
```
LIVE | MODELS
```

### 双版本
```
EDITION1 | EDITION2 | MODELS
```

---

## 🔧 技术实现细节

### Edition 2 AI Prompt 增强

```python
# 基础部分（与Edition 1相同）
- 当前价格
- 技术指标（MACD, RSI, EMA）
- 账户状态
- 当前持仓

# 新增部分（Edition 2专有）
- Fear & Greed Index
- 市场情绪分析
- 过去3分钟新闻（如果有）
- 根据新闻调整策略的提示
```

### 缓存机制

```python
# 避免频繁API调用
news_cache: 3分钟缓存
sentiment_cache: 5分钟缓存
fear_greed_cache: 1小时缓存
```

---

## ⚡ 性能对比

| 指标 | Edition 1 | Edition 2 |
|-----|----------|-----------|
| AI决策延迟 | ~5-10秒 | ~5-15秒 |
| 额外API调用 | 0 | 3个（已缓存）|
| Prompt长度 | ~1000 tokens | ~1500 tokens |
| 决策质量 | 基于技术指标 | 技术+新闻+情绪 |

---

## 🐛 已知问题和解决方案

### 问题1：Edition 2 决策错误
**原因**：account数据格式不匹配
**解决**：已修复，使用`account.get('balance', 100000)`

### 问题2：指标获取失败
**原因**：方法名不匹配（get_latest_indicator vs get_all_indicators）
**解决**：已修复，使用正确的API

### 问题3：新闻API超时
**原因**：DeepSeek思考模式需要更长时间
**解决**：已将timeout设置为90秒

---

## 📈 未来优化建议

### Edition 2 增强
1. 添加新闻重要性评分
2. 添加Twitter社交情绪
3. 添加链上数据分析
4. 添加宏观经济指标

### 用户体验
1. 在前端显示新闻ticker
2. 添加情绪指标可视化
3. 添加新闻提醒功能
4. 对比Edition 1和2的表现

---

## 🚢 AWS部署指南

### 步骤1：上传新文件

```bash
# 在本地
scp ai_trader_edition2.py ubuntu@你的AWS_IP:~/Trigo-Nexus/
scp app_dual_edition.py ubuntu@你的AWS_IP:~/Trigo-Nexus/
scp crypto_news.py ubuntu@你的AWS_IP:~/Trigo-Nexus/
scp templates/edition1.html ubuntu@你的AWS_IP:~/Trigo-Nexus/templates/
scp templates/edition2.html ubuntu@你的AWS_IP:~/Trigo-Nexus/templates/
```

### 步骤2：SSH到服务器并测试

```bash
ssh ubuntu@你的AWS_IP
cd ~/Trigo-Nexus
source venv/bin/activate

# 安装新依赖（如果需要）
pip install feedparser

# 测试运行
python app_dual_edition.py
# 按Ctrl+C停止
```

### 步骤3：修改systemd服务

```bash
sudo nano /etc/systemd/system/trigo-nexus.service
```

修改ExecStart行：
```ini
ExecStart=/home/ubuntu/Trigo-Nexus/venv/bin/python app_dual_edition.py
```

### 步骤4：重启服务

```bash
sudo systemctl daemon-reload
sudo systemctl restart trigo-nexus
sudo systemctl status trigo-nexus
```

### 步骤5：验证

访问：
- https://trigonexus.us/edition1
- https://trigonexus.us/edition2

---

## 📝 测试清单

### Edition 1 测试
- [ ] 页面正常加载
- [ ] 价格实时更新
- [ ] AI决策正常
- [ ] 交易执行成功
- [ ] 排行榜显示正确

### Edition 2 测试
- [ ] 页面正常加载
- [ ] 价格实时更新
- [ ] AI获取新闻成功
- [ ] AI获取Fear & Greed Index成功
- [ ] AI决策包含新闻分析
- [ ] 交易执行成功
- [ ] 新闻API路由工作正常

### 隔离测试
- [ ] Edition 1和2的数据不混淆
- [ ] 两个版本可以同时运行
- [ ] API路由正确分离
- [ ] 各自的trader独立工作

---

## 🎉 总结

### 完成的功能
✅ 创建完全隔离的双版本系统
✅ Edition 2集成新闻、Fear & Greed Index、市场情绪
✅ 独立的API路由和数据存储
✅ 友好的导航栏和页面标识
✅ 完整的错误处理和缓存机制

### 保障措施
✅ 数据完全隔离（独立实例）
✅ API完全隔离（独立路由）
✅ 线程完全隔离（独立循环）
✅ 不会互相干扰

### 优势
✅ Edition 1保持原有性能和稳定性
✅ Edition 2提供增强的决策能力
✅ 可以对比两个版本的表现
✅ 易于测试和部署

---

## 🔗 相关文件

- `ai_trader_edition2.py` - Edition 2 AI实现
- `app_dual_edition.py` - 双版本Flask应用
- `crypto_news.py` - 新闻API封装
- `templates/edition1.html` - Edition 1页面
- `templates/edition2.html` - Edition 2页面
- `start_dual_edition.sh` - 快速启动脚本

---

## 📞 需要帮助？

如果遇到问题：
1. 检查日志输出
2. 验证API keys
3. 检查网络连接
4. 确认所有依赖已安装

---

**最后更新**: 2025-10-26
**版本**: Dual Edition v1.0







