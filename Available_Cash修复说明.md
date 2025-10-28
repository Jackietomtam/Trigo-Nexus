# Available Cash 计算错误修复

## 🐛 问题描述

用户发现数据显示异常：
```
Total Account Value: $99,754.78
Available Cash: $99,765.15
```

**Available Cash 比 Total Account Value 还高！** 这明显不合理。

## 🔍 根本原因

### 错误的计算逻辑

**之前（错误）：**
```python
'available_cash': account['cash']
```

### 正确的概念模型

在保证金交易系统中：

1. **Total Cash (`account['cash']`)**
   - 初始资金
   - 减去：累计手续费
   - 加上：已实现盈亏
   - **不减去保证金**（保证金只是锁定，不是支出）

2. **Margin Used (`account['margin_used']`)**
   - 被锁定在持仓中的保证金
   - 开仓时增加，平仓时释放

3. **Available Cash（可用现金）**
   - **正确公式：`Available Cash = Total Cash - Margin Used`**
   - 这才是真正可以用于开新仓的资金

4. **Total Account Value（总账户价值）**
   - 公式：`Initial Balance - Fees + Realized P&L + Unrealized P&L`
   - 或者：`Cash + Unrealized P&L`（因为 cash 已经包含了 initial - fees + realized pnl）

## ✅ 修复方案

### 1. 后端 - `leverage_engine.py`

```python
# 修复 get_financial_metrics() 方法
'available_cash': account['cash'] - account['margin_used'],  # ✅ 正确
```

### 2. AI Prompt - `ai_trader_v2.py`

```python
# 计算真实可用现金
available_cash = account.get('cash', 0) - margin_used

prompt += f"""
Available Cash: {available_cash:.2f}
"""
```

### 3. 前端 - `static/js/app.js`

```javascript
// 使用后端计算好的 metrics.available_cash，或者手动计算
Available Cash: $${this.fn(metrics.available_cash ?? (account.cash - account.margin_used))}
```

### 4. 模板 - `templates/model_detail.html`

```javascript
Available Cash: $${fn((acc.cash||0) - (acc.margin_used||0))}
```

## 📊 修复前后对比

### 修复前（错误示例）

假设：
- Initial Balance: $100,000
- 手续费累计: $235
- 已实现盈亏: $0
- 未实现盈亏: -$10
- 保证金锁定: $23,485

**显示（错误）：**
- Total Cash: $99,765 (100,000 - 235)
- Available Cash: $99,765 ❌（错误！没有扣除锁定的保证金）
- Total Account Value: $99,755 (100,000 - 235 + 0 - 10)

**问题：** Available Cash > Total Account Value（荒谬！）

### 修复后（正确）

**显示（正确）：**
- Total Cash: $99,765 (100,000 - 235)
- **Available Cash: $76,280** ✅（99,765 - 23,485）
- Total Account Value: $99,755 (100,000 - 235 - 10)

**逻辑：** Available Cash < Total Account Value（合理！）

## 🎯 验证清单

部署后检查：

- [ ] 查看任意有持仓的账户
- [ ] 确认 `Available Cash < Total Account Value`
- [ ] 确认 `Available Cash = Total Cash - Margin Used`
- [ ] 尝试开新仓，确认使用的是正确的可用现金

## 💡 关键理解

| 指标 | 含义 | 公式 |
|------|------|------|
| **Total Cash** | 账户总现金 | Initial - Fees + Realized P&L |
| **Margin Used** | 锁定的保证金 | Sum of all positions' margins |
| **Available Cash** | 可用于开新仓 | **Total Cash - Margin Used** |
| **Total Account Value** | 账户总价值（权益） | Total Cash + Unrealized P&L |

## 🔗 相关文件

- `leverage_engine.py` (line 329)
- `ai_trader_v2.py` (line 216-222)
- `static/js/app.js` (line 1059)
- `templates/model_detail.html` (line 123)

---

**修复时间**: 2025-10-28
**影响范围**: 所有显示 Available Cash 的地方
**向后兼容**: ✅ 是（只是修正错误的计算）

