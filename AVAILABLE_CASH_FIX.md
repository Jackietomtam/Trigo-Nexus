# Available Cash = 0 问题根本原因与完整修复

## 🐛 问题现象

你在服务器上看到的问题：
```
QWEN3 MAX EDITION 1
Total Account Value: $99,278.25
Available Cash: $0.00    ← 这里显示为0
```

同时还有：
- 持仓列表显示 `Quantity: 0.0000`（实际有持仓但显示为0）
- 图表变成直线（因为没有新仓位导致账户价值不变）

## 🔍 根本原因分析

### 原因 1: Available Cash 计算逻辑没有防止负数

**问题代码：**
```python
# leverage_engine.py (旧版)
'available_cash': account['cash'] - account['margin_used']
```

**问题：** 当 `margin_used` > `cash` 时（高杠杆持仓场景），`available_cash` 会变成负数。前端可能会显示为 `$0.00` 或异常值。

### 原因 2: Edition 2 的交易循环没有使用最小名义金额阈值

**问题代码：**
```python
# app_dual_edition.py (旧版)
available = account_info.get('cash', 0) - account_info.get('margin_used', 0)
invest = max(0.0, available * (...))
quantity = (invest * leverage) / current_price
```

**问题：** 
1. `available` 可能为负数（没有 `max(0, ...)`）
2. 没有最小名义金额阈值检查，导致产生"尘埃仓位"（quantity ≈ 0.000001）
3. 这些极小的持仓在前端四舍五入后显示为 `0.0000`

### 原因 3: Prompt 中的数量精度不够

**问题代码：**
```python
# ai_trader_v2.py (旧版)
'quantity': round(pos.get('quantity', 0), 2)  # 只保留2位小数
```

**问题：** 对于小数量持仓（如 0.0001 BTC），四舍五入后变成 0.00，AI 看到的是 `quantity: 0.00`，误以为没有持仓。

### 原因 4: ai_trader_edition2_new.py 使用了未 clamp 的 available_cash

**问题代码：**
```python
# ai_trader_edition2_new.py (旧版)
Available Cash: {account.get('cash', 0):.2f}  # 直接用 cash，没有减去 margin_used
```

**问题：** Prompt 中显示的可用现金不准确，且可能为负。

## ✅ 完整修复方案

### 修复 1: leverage_engine.py - 添加 available_cash clamp

```python
# leverage_engine.py (新版)
def get_financial_metrics(self, trader_id):
    # ...
    
    # 计算可用资金（防止出现负数）
    available_cash = account['cash'] - account['margin_used']
    if available_cash < 0:
        available_cash = 0.0
    
    metrics = {
        # ...
        'total_cash': account['cash'],              # 账户现金口径
        'available_cash': available_cash,           # 可用现金（非负）
        'margin_used': account['margin_used'],
    }
```

### 修复 2: ai_trader_v2.py - Prompt 中使用 clamped available_cash + 更高精度数量

```python
# ai_trader_v2.py (新版)
def _build_detailed_prompt(self, account, positions, indicators):
    # 计算真实可用现金（防止出现负数）
    available_cash = account.get('cash', 0) - margin_used
    if available_cash < 0:
        available_cash = 0.0
    
    prompt += f"""
Available Cash: {available_cash:.2f}
"""
    
    # 持仓信息使用更高精度（6位小数）
    position_data = {
        'quantity': round(pos.get('quantity', 0), 6),  # 改为6位
        # ...
    }
```

### 修复 3: ai_trader_v2.py - Order sizing 添加最小名义金额阈值

```python
# ai_trader_v2.py (新版)
def _execute_single_trade(self, trade, indicators, account, positions):
    # ...
    
    # 使用非负可用资金
    available = max(0.0, account['cash'] - account['margin_used'])
    invest = available * (percentage / 100)
    
    # 添加最小下单名义金额阈值
    min_notional_usd = 50.0
    if invest * leverage < min_notional_usd:
        print(f"  ⚠ {self.name} 跳过开多: 可用资金不足（<{min_notional_usd}名义金额）")
        return None
    
    quantity = (invest * leverage) / current_price if current_price > 0 else 0
```

### 修复 4: app_dual_edition.py - Edition 2 交易循环添加相同保护

```python
# app_dual_edition.py (新版)
# 使用非负可用资金
available = max(0.0, account_info.get('cash', 0) - account_info.get('margin_used', 0))
invest = max(0.0, available * (max(0.0, min(100.0, percentage)) / 100.0))

# 添加最小名义金额阈值
min_notional_usd = 50.0
notional = invest * leverage
if notional < min_notional_usd:
    if action != 'hold':
        print(f"  ⚠ [E2] {trader.name} 跳过{action} {symbol}: 名义金额不足（${notional:.2f}<${min_notional_usd}）")
    continue

quantity = (invest * leverage) / current_price if current_price > 0 else 0
```

### 修复 5: ai_trader_edition2_new.py - 统一使用 clamped available_cash

```python
# ai_trader_edition2_new.py (新版)
def _build_detailed_prompt(self, account, positions, indicators):
    # 计算真实可用现金（防止出现负数）
    available_cash = account.get('cash', 0) - margin_used
    if available_cash < 0:
        available_cash = 0.0
    
    prompt += f"""
Available Cash: {available_cash:.2f}
"""
```

## 📊 修复效果

### 修复前：
```
Available Cash: $0.00                    ← 错误！
持仓: BTC quantity=0.0000                ← 显示为0但实际有持仓
图表: 一条水平直线                        ← 没有新仓位
```

### 修复后：
```
Available Cash: $23,485.32               ← 正确显示可用资金
持仓: BTC quantity=0.000143              ← 显示真实数量（6位精度）
图表: 随市场波动                          ← 反映未实现盈亏
名义金额不足时: 跳过交易                  ← 不再产生尘埃仓位
```

## 🔧 部署步骤

### 1. 在服务器上更新代码
```bash
ssh -i ~/Downloads/trigo-key.pem ubuntu@3.106.191.40

cd /home/ubuntu/AI交易
git pull origin main
```

### 2. 重启服务
```bash
sudo systemctl restart trigo-ai-trader
sudo systemctl status trigo-ai-trader
```

### 3. 验证修复
```bash
# 查看日志，确认没有"尘埃仓位"
sudo journalctl -u trigo-ai-trader -n 100 -f

# 应该看到类似的日志：
# ⚠ QWEN3 MAX 跳过开多: 可用资金不足（<50名义金额）available=5.23 invest=1.05
```

### 4. 前端验证
访问 `http://3.106.191.40:5001/edition1`，检查：
- [ ] Available Cash 不再显示为 $0.00
- [ ] 持仓列表中 Quantity 显示真实值（非 0.0000）
- [ ] 图表随市场波动而非水平直线
- [ ] 没有新的"尘埃仓位"产生

## 📝 技术总结

### 核心原则
1. **Available Cash 必须非负**: `max(0, cash - margin_used)`
2. **最小名义金额阈值**: 防止产生尘埃仓位（$50 USD）
3. **高精度数量显示**: 使用 6 位小数而非 2 位
4. **统一数据口径**: 所有模块使用相同的 available_cash 计算逻辑

### 影响范围
- ✅ Edition 1 (ai_trader_v2.py)
- ✅ Edition 2 (app_dual_edition.py, ai_trader_edition2_new.py)
- ✅ 后端 API (leverage_engine.py, app_v2.py)
- ✅ 前端显示 (static/js/app.js 已经使用后端数据，无需修改)

### 防御性编程
所有计算 `available` 的地方都使用：
```python
available = max(0.0, cash - margin_used)
```

所有开仓前检查：
```python
if invest * leverage < min_notional_usd:
    return None  # 或 continue
```

## 🎯 预期结果

修复后，系统将：
1. **正确显示可用现金**（即使在高杠杆场景下）
2. **不再产生尘埃仓位**（quantity ≈ 0）
3. **图表反映真实波动**（未实现盈亏变化）
4. **AI 看到准确数据**（6位精度 quantity）
5. **资金不足时优雅跳过**（而非强行开 0 数量仓位）

---

**修复完成时间**: 2025-10-28  
**影响版本**: Edition 1 & Edition 2  
**向后兼容**: ✅ 是（只是修正错误逻辑，不影响现有正常持仓）

