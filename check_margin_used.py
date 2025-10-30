#!/usr/bin/env python3
"""
检验 margin_used 计算是否正确
测试 Edition 1 和 Edition 2 的所有账户
"""

import sys
import os

# 导入引擎
from leverage_engine import LeverageEngine

def check_margin_used(engine, edition_name):
    """检查引擎中所有账户的 margin_used 是否正确"""
    print(f"\n{'='*70}")
    print(f"📊 检查 {edition_name} 的 margin_used")
    print(f"{'='*70}\n")
    
    issues_found = []
    
    for trader_id, positions in engine.positions.items():
        if trader_id not in engine.accounts:
            print(f"⚠️  Trader {trader_id} 有持仓但账户不存在")
            continue
        
        account = engine.accounts[trader_id]
        trader_name = account.get('name', f'Trader {trader_id}')
        
        # 计算实际保证金总和
        actual_margin = sum(pos.get('margin', 0) for pos in positions.values())
        current_margin_used = account['margin_used']
        
        print(f"🔍 [{trader_name}]")
        print(f"   持仓数量: {len(positions)}")
        print(f"   账户记录的 margin_used: ${current_margin_used:,.2f}")
        print(f"   实际持仓保证金总和: ${actual_margin:,.2f}")
        
        # 详细列出每个持仓
        if len(positions) > 0:
            print(f"   持仓明细:")
            for symbol, pos in positions.items():
                print(f"      • {symbol} {pos['side'].upper()} {pos['leverage']}x: "
                      f"qty={pos['quantity']:.6f}, "
                      f"entry=${pos['entry_price']:,.2f}, "
                      f"margin=${pos.get('margin', 0):,.2f}")
        
        # 检查差异
        diff = abs(current_margin_used - actual_margin)
        if diff > 0.01:  # 允许0.01的浮点误差
            print(f"   ❌ 发现问题！差异: ${diff:,.2f}")
            issues_found.append({
                'trader_name': trader_name,
                'current': current_margin_used,
                'actual': actual_margin,
                'diff': diff
            })
        else:
            print(f"   ✅ margin_used 正确")
        
        # 计算可用现金
        total_cash = account['cash']
        available_cash = total_cash - current_margin_used
        correct_available = total_cash - actual_margin
        
        print(f"   账户现金: ${total_cash:,.2f}")
        print(f"   当前显示的可用现金: ${available_cash:,.2f}")
        if diff > 0.01:
            print(f"   正确的可用现金应该是: ${correct_available:,.2f} (差异: ${correct_available - available_cash:,.2f})")
        
        print()
    
    # 检查没有持仓但 margin_used 不为0的账户
    for trader_id, account in engine.accounts.items():
        if trader_id not in engine.positions or len(engine.positions[trader_id]) == 0:
            trader_name = account.get('name', f'Trader {trader_id}')
            if account['margin_used'] != 0:
                print(f"⚠️  [{trader_name}] 没有持仓，但 margin_used = ${account['margin_used']:,.2f} (应该为0)")
                issues_found.append({
                    'trader_name': trader_name,
                    'current': account['margin_used'],
                    'actual': 0,
                    'diff': account['margin_used']
                })
    
    # 总结
    print(f"{'='*70}")
    if len(issues_found) == 0:
        print(f"✅ {edition_name}: 所有账户的 margin_used 都正确！")
    else:
        print(f"❌ {edition_name}: 发现 {len(issues_found)} 个账户的 margin_used 不正确：")
        for issue in issues_found:
            print(f"   • {issue['trader_name']}: "
                  f"${issue['current']:,.2f} -> ${issue['actual']:,.2f} "
                  f"(差异 ${issue['diff']:,.2f})")
    print(f"{'='*70}\n")
    
    return issues_found


def simulate_test():
    """模拟测试：创建测试数据并验证"""
    print("\n" + "="*70)
    print("🧪 模拟测试：创建测试场景")
    print("="*70 + "\n")
    
    # 创建测试引擎
    test_engine = LeverageEngine(initial_balance=100000)
    
    # 场景1：正常开仓
    print("📝 场景1：正常开仓")
    test_engine.create_account(1, "测试账户1")
    result = test_engine.open_position(1, 'BTC', 'long', 0.001, 110000, 10)
    if result['success']:
        print(f"   ✅ 开仓成功")
        account = test_engine.accounts[1]
        pos = test_engine.positions[1]['BTC']
        print(f"   保证金: ${pos['margin']:,.2f}")
        print(f"   margin_used: ${account['margin_used']:,.2f}")
        print(f"   可用现金: ${account['cash'] - account['margin_used']:,.2f}")
    
    # 场景2：开多个仓位
    print("\n📝 场景2：开多个仓位")
    test_engine.open_position(1, 'ETH', 'long', 0.1, 4000, 10)
    test_engine.open_position(1, 'SOL', 'short', 1.0, 200, 5)
    
    account = test_engine.accounts[1]
    total_margin = sum(pos.get('margin', 0) for pos in test_engine.positions[1].values())
    print(f"   持仓数量: {len(test_engine.positions[1])}")
    print(f"   实际保证金总和: ${total_margin:,.2f}")
    print(f"   margin_used: ${account['margin_used']:,.2f}")
    print(f"   匹配: {'✅' if abs(total_margin - account['margin_used']) < 0.01 else '❌'}")
    
    # 场景3：平仓后检查
    print("\n📝 场景3：平仓后检查 margin_used 是否正确释放")
    old_margin_used = account['margin_used']
    btc_margin = test_engine.positions[1]['BTC']['margin']
    print(f"   平仓前 margin_used: ${old_margin_used:,.2f}")
    print(f"   BTC持仓保证金: ${btc_margin:,.2f}")
    
    test_engine.close_position(1, 'BTC', 110500)
    new_margin_used = test_engine.accounts[1]['margin_used']
    expected_margin = old_margin_used - btc_margin
    
    print(f"   平仓后 margin_used: ${new_margin_used:,.2f}")
    print(f"   预期 margin_used: ${expected_margin:,.2f}")
    print(f"   释放正确: {'✅' if abs(new_margin_used - expected_margin) < 0.01 else '❌'}")
    
    # 场景4：手动破坏 margin_used 然后修复
    print("\n📝 场景4：模拟 margin_used 错误，然后测试修复功能")
    actual_margin = sum(pos.get('margin', 0) for pos in test_engine.positions[1].values())
    print(f"   当前正确的 margin_used: ${account['margin_used']:,.2f}")
    
    # 人为制造错误
    account['margin_used'] = account['margin_used'] + 50000  # 人为增加50000
    print(f"   人为破坏后的 margin_used: ${account['margin_used']:,.2f}")
    print(f"   可用现金变成: ${account['cash'] - account['margin_used']:,.2f} (错误！)")
    
    # 调用修复功能
    print("\n   🔧 调用 fix_margin_used_all() 修复...")
    test_engine.fix_margin_used_all()
    
    print(f"   修复后的 margin_used: ${account['margin_used']:,.2f}")
    print(f"   实际应该是: ${actual_margin:,.2f}")
    print(f"   修复成功: {'✅' if abs(account['margin_used'] - actual_margin) < 0.01 else '❌'}")
    print(f"   修复后可用现金: ${account['cash'] - account['margin_used']:,.2f}")
    
    print("\n" + "="*70)
    print("✅ 模拟测试完成")
    print("="*70 + "\n")


def main():
    """主函数"""
    print("\n" + "="*70)
    print("🔍 margin_used 计算检验程序")
    print("="*70)
    
    # 先运行模拟测试
    simulate_test()
    
    # 检查实际运行中的系统
    print("\n" + "="*70)
    print("📡 检查实际运行中的系统...")
    print("="*70 + "\n")
    
    try:
        # 尝试导入运行中的引擎实例
        print("⚠️  注意：此脚本需要在系统运行时检查实时数据")
        print("⚠️  如果系统未运行，将只看到模拟测试结果\n")
        
        # 这里可以添加对实际运行系统的检查
        # 但由于 app_dual_edition.py 的引擎实例在模块级别，
        # 我们需要在系统运行时才能访问
        
    except Exception as e:
        print(f"⚠️  无法访问运行中的系统: {e}")
        print("💡 提示：请在系统运行后，通过 API 或日志查看修复结果\n")
    
    print("\n" + "="*70)
    print("📋 总结")
    print("="*70)
    print("""
✅ 已完成的修复：

1. leverage_engine.py 中的 update_positions() 方法
   - 现在每次更新时都会重新计算并同步 margin_used
   - 如果发现不一致会自动修复并打印日志

2. 添加了 fix_margin_used_all() 方法
   - 可以手动调用来修复所有账户
   - 会详细显示修复前后的数据

3. 修复逻辑：
   margin_used = sum(实际持仓的保证金)
   available_cash = total_cash - margin_used

💡 建议的部署步骤：

1. 重启系统应用修复
2. 系统会在每次价格更新时自动检查并修复 margin_used
3. 查看日志中是否有 "🔧 [修复]" 的输出
4. 检查前端显示的 Available Cash 是否恢复正常

🔍 如何验证修复：

理论关系：
- Total Account Value = Initial Balance - Fees + Realized P&L + Unrealized P&L
- Available Cash = Total Cash - Margin Used
- Total Cash = Initial Balance - Fees + Realized P&L

预期结果（有持仓时）：
- Available Cash < Total Account Value (因为有保证金被锁定)
- Available Cash ≈ Total Account Value - 持仓保证金总和

如果只有1个小持仓(保证金~$6)，Available Cash 应该接近 Total Account Value
如果 Available Cash 只有 $18，说明有约 $98,555 的保证金被错误锁定
    """)
    print("="*70 + "\n")


if __name__ == '__main__':
    main()

