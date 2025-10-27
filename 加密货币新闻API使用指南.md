# 📰 加密货币新闻API使用指南

## 📋 目录

1. [API介绍](#api介绍)
2. [快速开始](#快速开始)
3. [API接口说明](#api接口说明)
4. [测试结果](#测试结果)
5. [集成到Trigo Nexus](#集成到trigo-nexus)

---

## 🎯 API介绍

### **数据来源：Tushare Pro**

Tushare Pro 提供6个加密货币新闻相关的接口：

| 接口 | 描述 | 更新频率 |
|------|------|----------|
| `jinse` | 金色财经资讯 | 5分钟 |
| `btc8` | 巴比特资讯 | 5分钟 |
| `bishijie` | 币世界资讯 | 5分钟 |
| `exchange_ann` | 交易所公告 | 5分钟 |
| `exchange_twitter` | 交易所Twitter | 5分钟 |
| `twitter_kol` | Twitter大V | 5分钟 |

---

## 🚀 快速开始

### **步骤1：注册Tushare Pro账号**

1. **访问注册页面**：
   ```
   https://tushare.pro/register
   ```

2. **填写注册信息**：
   - 手机号
   - 邮箱
   - 密码

3. **获取API Token**：
   - 登录后访问：https://tushare.pro/user/token
   - 复制你的Token（类似：`xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`）

---

### **步骤2：安装依赖**

在本地测试环境安装tushare：

```bash
cd '/Users/sogmac/Desktop/Agent-Test/AI交易'
source venv_local/bin/activate
pip install tushare
```

---

### **步骤3：配置Token**

编辑 `test_news_api.py` 文件：

```python
# 替换这一行
TUSHARE_TOKEN = "YOUR_TOKEN_HERE"

# 改为你的token
TUSHARE_TOKEN = "你的实际token"
```

---

### **步骤4：运行测试**

```bash
cd '/Users/sogmac/Desktop/Agent-Test/AI交易'
source venv_local/bin/activate
python test_news_api.py
```

---

## 📊 API接口说明

### **1. 金色财经 (jinse)**

```python
df = pro.jinse(
    start_date='2018-08-17 16:00:00',
    end_date='2018-08-17 18:00:00',
    fields='title, type, datetime'
)
```

**输出字段**：
- `title` - 标题
- `content` - 内容
- `type` - 类型（动态、声音、行情、分析等）
- `url` - URL
- `datetime` - 时间

**用途**：获取金色财经的即时新闻和市场动态

---

### **2. 巴比特 (btc8)**

```python
df = pro.btc8(
    start_date='2018-08-17 16:00:00',
    end_date='2018-08-17 18:00:00',
    fields='title, url, datetime'
)
```

**输出字段**：
- `title` - 标题
- `content` - 内容
- `type` - 类型
- `url` - URL
- `datetime` - 时间

**用途**：获取巴比特的深度分析文章

---

### **3. 币世界 (bishijie)**

```python
df = pro.bishijie(
    start_date='2018-08-17 16:00:00',
    end_date='2018-08-17 18:00:00',
    fields='title, datetime'
)
```

**输出字段**：
- `title` - 标题
- `content` - 内容
- `type` - 类型
- `url` - URL
- `datetime` - 时间

**用途**：获取币世界的快讯

---

### **4. 交易所公告 (exchange_ann)**

```python
df = pro.exchange_ann(
    start_date='2018-08-17 16:00:00',
    end_date='2018-08-17 18:00:00',
    fields='title, datetime'
)
```

**输出字段**：
- `title` - 标题
- `content` - 内容
- `type` - 类型
- `url` - URL
- `datetime` - 时间

**用途**：获取各大交易所的官方公告（上币、下币、维护等）

---

### **5. 交易所Twitter (exchange_twitter)**

```python
df = pro.exchange_twitter(
    start_date='2018-09-02 03:20:03',
    end_date='2018-09-02 03:35:03',
    fields='id, account, nickname, content, str_posted_at'
)
```

**输出字段**：
- `id` - 记录ID
- `account_id` - 交易所账号ID
- `account` - 交易所账号
- `nickname` - 交易所昵称
- `avatar` - 头像
- `content_id` - 内容ID
- `content` - 原始内容
- `is_retweet` - 是否转发
- `retweet_content` - 转发内容（JSON）
- `media` - 附件（JSON）
- `posted_at` - 发布时间戳
- `str_posted_at` - 发布时间
- `create_at` - 采集时间

**用途**：获取各大交易所官方Twitter消息

---

### **6. Twitter大V (twitter_kol)**

```python
df = pro.twitter_kol(
    start_date='2018-09-26 14:15:41',
    end_date='2018-09-26 16:20:11',
    fields='id, account, nickname, content, str_posted_at'
)
```

**输出字段**：
- `id` - 记录ID
- `account_id` - 账号ID
- `account` - 账号
- `nickname` - 昵称
- `avatar` - 头像
- `content` - 原始内容
- `is_retweet` - 是否转发
- `retweet_content` - 转发内容（JSON）
- `media` - 附件（JSON）
- `posted_at` - 发布时间戳
- `str_posted_at` - 发布时间
- `create_at` - 采集时间

**用途**：获取加密货币领域意见领袖的Twitter消息

---

## ⚠️ 使用限制

1. **时间范围必选**：
   - 必须指定`start_date`和`end_date`
   - 格式：`YYYY-MM-DD HH:MM:SS`

2. **数据量限制**：
   - 每次最多返回**200条**数据
   - 如需更多，需要分批请求

3. **更新频率**：
   - 所有接口：5分钟更新一次
   - 不适合高频交易（适合中长期分析）

4. **API限制**：
   - 免费版可能有调用次数限制
   - 详情查看：https://tushare.pro/document/2

---

## 📈 测试结果示例

### **金色财经示例数据**：

```
                             title                  type             datetime
0   OMO智能合约使以太坊交易费用大幅增加             动态    2018-08-17 17:49:21
1   币威美国 CSO：钱包是下一个区块链千万级社群      声音    2018-08-17 17:35:06
2   OKCoin大量币种上涨YOYO的24H涨幅达到13,611.22%   行情    2018-08-17 17:29:22
```

### **巴比特示例数据**：

```
                               title                                  url
0  中国太保携手京东上线区块链专用发票电子化项目   https://www.8btc.com/article/255078
1  OKCoin韩国交易所多币种放量上涨，YOYO涨幅最高达22122.22%  https://www.8btc.com/article/255072
```

---

## 🔌 集成到Trigo Nexus

### **方案1：作为情绪分析指标**

将新闻数据转换为市场情绪指标：

```python
import tushare as ts
from datetime import datetime, timedelta

class NewsAnalyzer:
    def __init__(self, token):
        self.pro = ts.pro_api(token)
    
    def get_latest_news(self, hours=1):
        """获取最近N小时的新闻"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        start_date = start_time.strftime('%Y-%m-%d %H:%M:%S')
        end_date = end_time.strftime('%Y-%m-%d %H:%M:%S')
        
        # 合并所有新闻源
        all_news = []
        
        try:
            # 金色财经
            df = self.pro.jinse(start_date=start_date, end_date=end_date)
            if df is not None:
                all_news.extend(df['title'].tolist())
        except:
            pass
        
        return all_news
    
    def analyze_sentiment(self, news_list):
        """分析新闻情绪（简单版本）"""
        positive_keywords = ['上涨', '利好', '突破', '创新高', '增长']
        negative_keywords = ['下跌', '利空', '暴跌', '下滑', '警告']
        
        positive_count = 0
        negative_count = 0
        
        for news in news_list:
            if any(kw in news for kw in positive_keywords):
                positive_count += 1
            if any(kw in news for kw in negative_keywords):
                negative_count += 1
        
        # 计算情绪分数（-1到1）
        total = positive_count + negative_count
        if total == 0:
            return 0
        
        sentiment_score = (positive_count - negative_count) / total
        return sentiment_score
```

---

### **方案2：作为AI交易决策参考**

将新闻摘要添加到AI交易员的prompt中：

```python
def build_trading_prompt_with_news(self, indicators, news_summary):
    """构建包含新闻的交易prompt"""
    
    prompt = f"""
你是一个专业的加密货币交易员。

【市场技术指标】
{indicators}

【最新市场新闻】（最近1小时）
{news_summary}

基于以上技术指标和市场新闻，做出交易决策...
"""
    return prompt
```

---

### **方案3：新闻提醒功能**

添加重要新闻提醒到前端：

```python
def get_important_news(self):
    """获取重要新闻"""
    # 获取交易所公告（最重要）
    df = self.pro.exchange_ann(
        start_date=...,
        end_date=...
    )
    
    # 筛选重要关键词
    important_keywords = ['上币', '下币', '维护', '分叉', '空投']
    
    important_news = []
    for _, row in df.iterrows():
        if any(kw in row['title'] for kw in important_keywords):
            important_news.append({
                'title': row['title'],
                'datetime': row['datetime']
            })
    
    return important_news
```

---

## 💡 使用建议

### **适合的应用场景**：

✅ **中长期交易决策**
   - 新闻作为辅助判断
   - 情绪分析

✅ **风险事件监控**
   - 交易所公告
   - 重大新闻提醒

✅ **市场研究**
   - 历史事件分析
   - 舆情追踪

### **不适合的场景**：

❌ **高频交易**
   - 5分钟更新太慢
   - 延迟较大

❌ **实时套利**
   - 数据不够实时
   - 不如直接用价格API

---

## 🎯 下一步

1. **注册Tushare Pro账号** → https://tushare.pro/register
2. **获取API Token**
3. **运行测试脚本** → `python test_news_api.py`
4. **查看测试结果**
5. **考虑是否集成到Trigo Nexus**

---

## 📞 相关链接

- **Tushare Pro官网**: https://tushare.pro
- **API文档**: https://tushare.pro/document/2
- **注册链接**: https://tushare.pro/register
- **Token管理**: https://tushare.pro/user/token

---

**最后更新**: 2025-10-26

