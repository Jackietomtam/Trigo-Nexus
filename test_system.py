"""
系统测试脚本
验证所有组件是否正常工作
"""

import sys

def test_imports():
    """测试所有依赖是否正确安装"""
    print("正在测试依赖...")
    
    try:
        import flask
        print("  ✓ Flask")
    except ImportError as e:
        print(f"  ✗ Flask: {e}")
        return False
    
    try:
        import flask_socketio
        print("  ✓ Flask-SocketIO")
    except ImportError as e:
        print(f"  ✗ Flask-SocketIO: {e}")
        return False
    
    try:
        import requests
        print("  ✓ Requests")
    except ImportError as e:
        print(f"  ✗ Requests: {e}")
        return False
    
    try:
        import finnhub
        print("  ✓ Finnhub")
    except ImportError as e:
        print(f"  ✗ Finnhub: {e}")
        return False
    
    return True

def test_config():
    """测试配置文件"""
    print("\n正在测试配置...")
    
    try:
        import config
        
        if config.OPENROUTER_API_KEY:
            print("  ✓ OpenRouter API 密钥已配置")
        else:
            print("  ✗ OpenRouter API 密钥未配置")
            return False
        
        if config.FINNHUB_API_KEY:
            print("  ✓ Finnhub API 密钥已配置")
        else:
            print("  ✗ Finnhub API 密钥未配置")
            return False
        
        print(f"  ✓ 初始资金: ${config.INITIAL_BALANCE:,}")
        print(f"  ✓ 交易间隔: {config.TRADING_INTERVAL} 秒")
        print(f"  ✓ AI 数量: {config.NUM_AI_TRADERS}")
        print(f"  ✓ 支持币种: {len(config.SUPPORTED_CRYPTOS)} 种")
        
        return True
    except Exception as e:
        print(f"  ✗ 配置错误: {e}")
        return False

def test_modules():
    """测试核心模块"""
    print("\n正在测试核心模块...")
    
    try:
        from market_data import MarketData
        print("  ✓ 市场数据模块")
        
        # 测试获取价格
        market = MarketData()
        price = market.get_crypto_price('BTC')
        if price and price > 0:
            print(f"    BTC 价格: ${price:,.2f}")
        
    except Exception as e:
        print(f"  ✗ 市场数据模块: {e}")
        return False
    
    try:
        from trading_engine import TradingEngine
        print("  ✓ 交易引擎模块")
        
        # 测试创建账户
        engine = TradingEngine(100000)
        account = engine.create_account(1, "Test Trader")
        if account['balance'] == 100000:
            print(f"    测试账户创建成功")
        
    except Exception as e:
        print(f"  ✗ 交易引擎模块: {e}")
        return False
    
    try:
        from ai_trader import AITrader
        print("  ✓ AI 交易代理模块")
    except Exception as e:
        print(f"  ✗ AI 交易代理模块: {e}")
        return False
    
    return True

def test_files():
    """测试文件结构"""
    print("\n正在测试文件结构...")
    
    import os
    
    required_files = [
        'app.py',
        'config.py',
        'market_data.py',
        'trading_engine.py',
        'ai_trader.py',
        'requirements.txt',
        'templates/index.html',
        'static/css/style.css',
        'static/js/app.js'
    ]
    
    all_exist = True
    for file in required_files:
        if os.path.exists(file):
            print(f"  ✓ {file}")
        else:
            print(f"  ✗ {file} 不存在")
            all_exist = False
    
    return all_exist

def main():
    """运行所有测试"""
    print("═" * 60)
    print("  🧪 AI 交易系统测试")
    print("═" * 60)
    print()
    
    # 运行测试
    tests = [
        ("依赖库", test_imports),
        ("配置文件", test_config),
        ("核心模块", test_modules),
        ("文件结构", test_files)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n测试 {name} 时出错: {e}")
            results.append((name, False))
    
    # 显示结果
    print("\n" + "═" * 60)
    print("  📊 测试结果")
    print("═" * 60)
    print()
    
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {name:20s} {status}")
    
    print()
    all_passed = all(r[1] for r in results)
    
    if all_passed:
        print("🎉 所有测试通过！系统已准备就绪。")
        print()
        print("现在运行：python app.py")
        print("然后访问：http://localhost:5000")
        return 0
    else:
        print("⚠️  部分测试失败，请检查错误信息。")
        return 1

if __name__ == "__main__":
    sys.exit(main())



