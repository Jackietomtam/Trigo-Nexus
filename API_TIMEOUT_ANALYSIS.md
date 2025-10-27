# API超时问题分析

## 🔍 问题现象

Edition 1和Edition 2中，偶尔会出现AI调用失败，提示：
```
AI API调用失败: HTTPSConnectionPool(host='dashscope.aliyuncs.com', port=443): 
Read timed out. (read timeout=90)
```

导致该轮次的AI决策失败，聊天历史中缺失记录。

---

## 📊 超时统计

**最近15分钟内：4次超时**
- QWEN超时：2次
- DEEPSEEK超时：2次

---

## 🎯 根本原因分析

### 1. **阿里云API响应慢**

**时间线分析（以03:48-03:49的案例为例）：**

```
03:48:26 - Edition 1 QWEN 调用API
03:48:28 - Edition 2 QWEN 调用API（几乎同时）
           ↓
           等待89秒...
           ↓
03:49:57 - Edition 1 QWEN 超时 ❌
03:49:58 - Edition 2 QWEN 超时 ❌
```

**发现：**
- API调用后需要等待**89秒才超时**（接近90秒的超时限制）
- 说明**阿里云DashScope API响应非常慢**
- 两个模型**几乎同时**调用API，都遇到了响应慢的问题

---

### 2. **并发请求可能加剧问题**

**当前架构：**
- Edition 1和Edition 2**几乎同时**触发AI决策（时间差2秒）
- 每个Edition有2个AI（QWEN + DEEPSEEK）
- 总共**4个API请求在短时间内发出**：
  1. Edition 1 QWEN
  2. Edition 1 DEEPSEEK（等QWEN完成后）
  3. Edition 2 QWEN
  4. Edition 2 DEEPSEEK（等QWEN完成后）

**问题：**
- Edition 1和2的QWEN**几乎同时调用API**（03:48:26和03:48:28）
- 如果QWEN的请求很慢，会阻塞后续的DEEPSEEK请求
- 多个并发请求可能导致阿里云API响应更慢

---

### 3. **DeepSeek的"思考模式"需要更长时间**

代码中已经注意到：
```python
# DeepSeek使用阿里云百炼API（思考模式需要更长时间）
"extra_body": {"enable_thinking": True}
timeout=90  # 增加到90秒，因为思考模式需要更长时间
```

**但实际情况：**
- 90秒的超时对于某些复杂请求**仍然不够**
- DeepSeek的思考模式确实需要更长时间处理

---

### 4. **Prompt复杂度**

超时时的prompt长度：
- Edition 1 QWEN: **7090字符**
- Edition 2 QWEN: **7217字符**

随着持仓增多，prompt会包含：
- 6个币种的技术指标
- 多个持仓的详细信息
- 市场分析要求

**越复杂的prompt，AI处理时间越长。**

---

## 💡 为什么超时

### 综合原因：

1. **阿里云API服务端响应慢**
   - 可能是服务器负载高
   - 可能是模型计算时间长
   - 可能是网络延迟（AWS到阿里云）

2. **并发请求加剧问题**
   - 4个AI几乎同时请求
   - 可能触发API的限流机制
   - 多个请求竞争资源

3. **DeepSeek思考模式耗时**
   - "enable_thinking" 模式需要更长时间
   - 90秒可能不够

4. **Prompt复杂度增加**
   - 随着交易进行，持仓增多
   - Prompt变长，处理时间增加

---

## ✅ 当前的临时解决方案

**已实施（c7ca2c7提交）：**
- API调用失败时，保存错误记录到聊天历史
- 用户可以看到：`⚠️ AI调用失败（API超时或网络错误），本轮跳过决策`
- 不会再出现"某一轮完全消失"的情况

---

## 🚀 建议的长期解决方案

### 方案1：增加超时时间 ⭐ 最简单
```python
timeout=120  # 从90秒增加到120秒
```

**优点：** 简单直接
**缺点：** 治标不治本，还是可能超时

---

### 方案2：添加重试机制 ⭐⭐ 推荐
```python
for retry in range(3):  # 重试3次
    try:
        response = requests.post(..., timeout=90)
        if response.status_code == 200:
            break
    except Timeout:
        if retry < 2:
            time.sleep(5)  # 等待5秒后重试
            continue
        else:
            return None  # 3次都失败才放弃
```

**优点：** 提高成功率
**缺点：** 可能延长决策时间

---

### 方案3：使用异步并行请求 ⭐⭐⭐ 最优
```python
import concurrent.futures

with ThreadPoolExecutor(max_workers=2) as executor:
    future_qwen = executor.submit(qwen_trader.make_decision)
    future_deepseek = executor.submit(deepseek_trader.make_decision)
    
    qwen_result = future_qwen.result()
    deepseek_result = future_deepseek.result()
```

**优点：**
- 两个AI真正并行执行
- 总时间 = max(QWEN时间, DEEPSEEK时间)
- 不会因为一个慢而影响另一个

**缺点：** 需要修改交易循环架构

---

### 方案4：降低并发压力 ⭐⭐
```python
# Edition 1先决策，完成后Edition 2再决策
# 或者错开时间：Edition 1在00:00, 03:00, 06:00
#              Edition 2在01:30, 04:30, 07:30
```

**优点：** 降低阿里云API的并发压力
**缺点：** 两个Edition不能同时对比

---

### 方案5：备用API ⭐⭐⭐
```python
try:
    # 优先使用阿里云
    response = call_aliyun_api()
except Timeout:
    # 失败后切换到OpenRouter或其他API
    response = call_backup_api()
```

**优点：** 高可用性，一个API失败自动切换
**缺点：** 需要集成多个API

---

## 📈 监控建议

添加成功率统计：
```python
# 统计每个AI的调用成功率
{
    "QWEN3 MAX": {
        "total_calls": 100,
        "successful": 95,
        "timeout": 3,
        "error": 2,
        "success_rate": "95%"
    },
    "DEEPSEEK V3.2": {
        "total_calls": 100,
        "successful": 93,
        "timeout": 5,
        "error": 2,
        "success_rate": "93%"
    }
}
```

---

## 🎯 结论

**超时原因：**
1. 阿里云API响应慢（主要原因）
2. 并发请求过多（加剧因素）
3. DeepSeek思考模式耗时长（特定因素）
4. Prompt复杂度增加（持续因素）

**当前状态：**
- ✅ 用户能看到失败记录，不会困惑
- ⚠️ 超时问题仍会发生

**推荐优先级：**
1. **立即：增加超时到120秒**（简单快速）
2. **短期：添加重试机制**（提高成功率）
3. **中期：改为异步并行请求**（架构优化）
4. **长期：集成备用API**（高可用性）

