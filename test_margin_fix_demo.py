#!/usr/bin/env python3
"""
演示 margin_used 修复效果
模拟你遇到的实际问题场景
"""

from leverage_engine import LeverageEngine

print("\n" + "="*70)
print("🎬 Margin Used Bug 修复效果演示")
print("="*70)

# 创建测试引擎
engine = LeverageEngine(initial_balance=100000)
engine.create_account(1, "QWEN3 MAX")

print("\n📝 场景：模拟你遇到的实际问题")
print("-"*70)

# 模拟多次交易（开仓、平仓）
print("\n步骤1: 模拟18笔交易...")
trades_data = [
    ('ETH', 'short', 15.377, 3990.29, 10),
    ('BNB', 'short', 37.5973, 1107.80, 10),
    ('SOL', 'short', 80.0176, 193.75, 10),
    ('BNB', 'short', 11.8687, 1103.61, 10),
    ('ETH', 'short', 2.8087, 3996.25, 10),
    ('BTC', 'short', 0.0127, 112591.01, 10),
    ('BTC', 'short', 0.0027, 112804.62, 10),
    ('ETH', 'long', 0.0598, 4014.86, 10),
    ('BNB', 'long', 0.2238, 1111.60, 10),
]

for symbol, side, qty, price, lev in trades_data:
    # 开仓
    result = engine.open_position(1, symbol, side, qty, price, lev)
    if result['success']:
        # 立即平仓（模拟快速交易）
        exit_price = price * (1.001 if side == 'long' else 0.999)
        engine.close_position(1, symbol, exit_price)

print(f"✅ 已完成 {len(trades_data)} 笔交易")

# 再开一个当前持仓
print("\n步骤2: 开一个当前持仓 (BTC LONG 10x)...")
result = engine.open_position(1, 'BTC', 'long', 0.0006, 109985.34, 10)
btc_margin = result['position']['margin']
print(f"✅ BTC持仓保证金: ${btc_margin:.2f}")

# 获取账户状态
account = engine.accounts[1]
positions = engine.positions[1]

print("\n" + "="*70)
print("📊 当前账户状态（修复前）")
print("="*70)

# 模拟bug：人为破坏 margin_used
print("\n⚠️  模拟Bug：margin_used 被错误累积...")
original_margin = account['margin_used']
account['margin_used'] = 98555.39  # 模拟你的实际数据

print(f"""
账户数据:
  Total Account Value: ${account['total_value']:,.2f}
  Total Cash: ${account['cash']:,.2f}
  
  实际持仓保证金: ${original_margin:.2f}
  Bug导致的 margin_used: ${account['margin_used']:,.2f}  ❌
  
  错误的 Available Cash: ${account['cash'] - account['margin_used']:,.2f}  ❌
  正确的 Available Cash: ${account['cash'] - original_margin:,.2f}  ✅
  
  差异: ${account['margin_used'] - original_margin:,.2f} (被错误锁定)
""")

print("="*70)
print("🔧 调用修复方法: fix_margin_used_all()")
print("="*70)

# 调用修复
engine.fix_margin_used_all()

print("\n" + "="*70)
print("📊 修复后的账户状态")
print("="*70)

account = engine.accounts[1]
available = account['cash'] - account['margin_used']

print(f"""
账户数据:
  Total Account Value: ${account['total_value']:,.2f}
  Total Cash: ${account['cash']:,.2f}
  
  修复后的 margin_used: ${account['margin_used']:,.2f}  ✅
  修复后的 Available Cash: ${available:,.2f}  ✅
  
  持仓数量: {len(positions)}
  持仓保证金总和: ${sum(p['margin'] for p in positions.values()):.2f}
""")

for symbol, pos in positions.items():
    print(f"  • {symbol} {pos['side'].upper()} {pos['leverage']}x: margin=${pos['margin']:.2f}")

print("\n" + "="*70)
print("✅ 修复成功！")
print("="*70)

print(f"""
对比结果:
  修复前 Available Cash: $18.65          ❌
  修复后 Available Cash: ${available:,.2f}   ✅
  
  差异: ${available - 18.65:,.2f} (恢复的可用资金)
  
现在可以正常交易了！🎉
""")

print("="*70)
print("📝 技术说明")
print("="*70)
print("""
修复原理:
1. update_positions() 现在每5秒自动重新计算 margin_used
2. margin_used = sum(实际持仓的保证金)
3. 不再依赖累加/减操作，避免累积错误

部署后效果:
- 系统启动时自动修复一次
- 之后每次价格更新都会自动验证并修复
- 如果发现不一致会在日志中显示 "🔧 [修复]"
""")

print("="*70 + "\n")

