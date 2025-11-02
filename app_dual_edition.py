"""
Trigo Nexus - Edition 1
AI交易系统（带新闻功能）
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import threading
import time
import os

# 导入模块
from market_data import MarketData
from kline_data import KLineData
from leverage_engine import LeverageEngine
from order_manager import OrderManager

# 强制重新加载Edition 2模块以避免缓存问题
import sys
if 'ai_trader_edition2' in sys.modules:
    del sys.modules['ai_trader_edition2']
    
from ai_trader_edition2 import AITraderEdition2
from crypto_news import CryptoNewsAPI
from config import INITIAL_BALANCE, TRADING_INTERVAL, AI_MODELS

app = Flask(__name__)
app.config['SECRET_KEY'] = 'trigo-nexus-edition1'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# ========================================
# Edition 1 系统实例
# ========================================
market_data = MarketData()
kline_data = KLineData(market_data)
leverage_engine = LeverageEngine(INITIAL_BALANCE)
order_manager = OrderManager(leverage_engine)
ai_traders = []
system_running = False
competition_stats = {
    'start_time': None,
    'total_trades': 0,
    'invocations': 0
}

# 新闻API
news_api = CryptoNewsAPI()

# 模型slug映射
MODEL_SLUGS = {
    'qwen3-max': 1,
    'deepseek-chat-v3.1': 2,
    'deepseek-v3': 2
}

def initialize_traders():
    """初始化Edition 1交易员（带新闻功能）"""
    global ai_traders
    ai_traders = []
    
    print("\n📦 初始化 Edition 1 交易员（带新闻功能）...")
    for model_config in AI_MODELS:
        trader_id = model_config['id']
        leverage_engine.create_account(trader_id, model_config['name'])
        
        # 获取账户信息
        account_data = leverage_engine.accounts.get(trader_id, {})
        
        trader = AITraderEdition2(
            model_id=trader_id,
            name=model_config['name'],
            model=model_config['model'],
            strategy=model_config['strategy'],
            account=account_data,
            leverage_engine=leverage_engine,
            kline_data=kline_data,
            order_manager=order_manager
        )
        
        # 包装make_decision方法（使用闭包正确捕获trader）
        def create_wrapped_make_decision(trader_instance):
            def wrapped_make_decision():
                # 每次调用时更新账户信息
                trader_instance.account = leverage_engine.accounts.get(trader_instance.trader_id, {})
                return trader_instance.make_decision()
            return wrapped_make_decision
        
        trader.make_decision_wrapped = create_wrapped_make_decision(trader)
        
        ai_traders.append(trader)
        print(f"  ✓ {trader.name} ({model_config['model']})")
    
    print(f"✓ Edition 1: 已初始化 {len(ai_traders)} 个AI交易员（带新闻功能）")

def trading_loop():
    """Edition 1 交易循环（带新闻）"""
    global system_running, competition_stats
    
    print("🚀 Edition 1 系统启动（带新闻功能）...", flush=True)
    competition_stats['start_time'] = time.time()
    
    # AI决策间隔控制（每3分钟决策一次）
    AI_DECISION_INTERVAL = 180  # 秒（3分钟）
    last_ai_decision_time = 0
    
    while system_running:
        try:
            print(f"\n⏰ 交易周期 #{competition_stats['invocations']}", flush=True)
            competition_stats['invocations'] += 1
            
            kline_data.update_klines()
            current_prices = market_data.get_all_prices()
            leverage_engine.update_positions(current_prices)
            triggered = order_manager.check_orders(current_prices)
            
            # 检查是否需要进行AI决策
            current_time = time.time()
            should_make_decision = (current_time - last_ai_decision_time) >= AI_DECISION_INTERVAL
            
            if not should_make_decision:
                print(f"  ⏳ 跳过AI决策（距上次{int(current_time - last_ai_decision_time)}秒）", flush=True)
                time.sleep(TRADING_INTERVAL)
                continue
            
            last_ai_decision_time = current_time
            print(f"🤖 开始AI决策（含新闻）...", flush=True)
            print(f"  🔍 traders数量: {len(ai_traders)}, 名单: {[t.name for t in ai_traders]}", flush=True)
            for trader in ai_traders:
                try:
                    print(f"  🎯 正在处理: {trader.name} (ID: {trader.trader_id})", flush=True)
                    decision = trader.make_decision_wrapped()
                    if not decision:
                        continue
                    
                    # 检查decision格式
                    if not isinstance(decision, dict):
                        print(f"  ⚠️ {trader.name} 决策格式错误: {type(decision)}", flush=True)
                        continue
                    
                    if 'decisions' not in decision:
                        print(f"  ⚠️ {trader.name} 决策缺少'decisions'字段", flush=True)
                        continue
                    
                    if not isinstance(decision['decisions'], dict):
                        print(f"  ⚠️ {trader.name} 'decisions'不是字典: {type(decision['decisions'])}", flush=True)
                        continue
                    
                    if decision and 'decisions' in decision:
                        # 获取当前持仓（字典：symbol -> position）
                        current_positions = leverage_engine.get_positions(trader.trader_id)
                        position_symbols = {sym: pos for sym, pos in current_positions.items()}
                        account_info = leverage_engine.accounts.get(trader.trader_id, {})
                        
                        # 执行交易决策
                        for symbol, signal in decision['decisions'].items():
                            has_position = symbol in position_symbols
                            current_price = current_prices.get(symbol)
                            if not current_price:
                                continue
                            
                            action = str(signal.get('signal', 'hold')).lower()
                            leverage = int(signal.get('leverage', 10))
                            percentage = float(signal.get('percentage', 0))
                            # 使用非负可用资金
                            available = max(0.0, account_info.get('cash', 0) - account_info.get('margin_used', 0))
                            invest = max(0.0, available * (max(0.0, min(100.0, percentage)) / 100.0))
                            
                            # 添加最小名义金额阈值，避免产生"尘埃仓位"
                            min_notional_usd = 50.0
                            notional = invest * leverage
                            if notional < min_notional_usd:
                                if action != 'hold':
                                    print(f"  ⚠ {trader.name} 跳过{action} {symbol}: 名义金额不足（${notional:.2f}<${min_notional_usd}）", flush=True)
                                continue
                            
                            quantity = (invest * leverage) / current_price if current_price > 0 else 0
                            
                            if action == 'long':
                                if not has_position:
                                    if quantity <= 0:
                                        continue
                                    print(f"  → {trader.name} 开多 {symbol} {leverage}x", flush=True)
                                    leverage_engine.open_position(
                                        trader.trader_id, symbol, 'long', quantity, current_price, leverage,
                                        profit_target=current_price * 1.10,
                                        stop_loss=current_price * 0.95,
                                        invalidation_condition=f"价格跌破 ${current_price*0.95:.2f}",
                                        confidence=signal.get('confidence', 0.7),
                                        risk_usd=invest * 0.05,
                                        reason=decision.get('analysis', '')[:200]
                                    )
                                elif position_symbols[symbol]['side'] == 'short':
                                    print(f"  → {trader.name} 平空 {symbol}", flush=True)
                                    leverage_engine.close_position(trader.trader_id, symbol, current_price)
                                    if quantity > 0:
                                        print(f"  → {trader.name} 开多 {symbol} {leverage}x", flush=True)
                                        leverage_engine.open_position(
                                            trader.trader_id, symbol, 'long', quantity, current_price, leverage,
                                            profit_target=current_price * 1.10,
                                            stop_loss=current_price * 0.95,
                                            invalidation_condition=f"价格跌破 ${current_price*0.95:.2f}",
                                            confidence=signal.get('confidence', 0.7),
                                            risk_usd=invest * 0.05,
                                            reason=decision.get('analysis', '')[:200]
                                        )
                            elif action == 'short':
                                if not has_position:
                                    if quantity <= 0:
                                        continue
                                    print(f"  → {trader.name} 开空 {symbol} {leverage}x", flush=True)
                                    leverage_engine.open_position(
                                        trader.trader_id, symbol, 'short', quantity, current_price, leverage,
                                        profit_target=current_price * 0.90,
                                        stop_loss=current_price * 1.05,
                                        invalidation_condition=f"价格突破 ${current_price*1.05:.2f}",
                                        confidence=signal.get('confidence', 0.7),
                                        risk_usd=invest * 0.05,
                                        reason=decision.get('analysis', '')[:200]
                                    )
                                elif position_symbols[symbol]['side'] == 'long':
                                    print(f"  → {trader.name} 平多 {symbol}", flush=True)
                                    leverage_engine.close_position(trader.trader_id, symbol, current_price)
                                    if quantity > 0:
                                        print(f"  → {trader.name} 开空 {symbol} {leverage}x", flush=True)
                                        leverage_engine.open_position(
                                            trader.trader_id, symbol, 'short', quantity, current_price, leverage,
                                            profit_target=current_price * 0.90,
                                            stop_loss=current_price * 1.05,
                                            invalidation_condition=f"价格突破 ${current_price*1.05:.2f}",
                                            confidence=signal.get('confidence', 0.7),
                                            risk_usd=invest * 0.05,
                                            reason=decision.get('analysis', '')[:200]
                                        )
                            else:  # hold
                                # 不做任何操作；绝不因为 hold 主动平仓
                                pass
                        
                        print(f"  ✓ {trader.name} 决策完成", flush=True)
                        
                except Exception as e:
                    print(f"  ❌ {trader.name} 决策错误: {e}", flush=True)
            
            # 广播更新
            socketio.emit('edition2_update', {
                'prices': current_prices,
                'leaderboard': leverage_engine.get_leaderboard(),
                'stats': competition_stats
            }, namespace='/')
            
            print(f"✓ 周期完成", flush=True)
            time.sleep(TRADING_INTERVAL)
            
        except Exception as e:
            print(f"❌ 交易循环错误: {e}", flush=True)
            time.sleep(10)

# ========================================
# 路由 - Edition 1
# ========================================
@app.route('/')
@app.route('/edition2')  # 兼容旧链接
def home_page():
    return render_template('edition2.html')

@app.route('/api/edition2/prices')
def api_prices():
    prices = market_data.get_all_prices()
    changes = {sym: market_data.get_price_change(sym) for sym in prices.keys()}
    return jsonify({'prices': prices, 'changes': changes})

@app.route('/api/edition2/leaderboard')
def api_leaderboard():
    try:
        current_prices = market_data.get_all_prices()
        leverage_engine.update_positions(current_prices)
    except Exception as e:
        print(f"⚠️ leaderboard价格更新失败: {e}, 使用缓存数据", flush=True)
    return jsonify(leverage_engine.get_leaderboard())

@app.route('/api/edition2/trades')
def api_trades():
    return jsonify(leverage_engine.get_trades(100))

@app.route('/api/edition2/chat')
def api_chat():
    # 聚合真实对话
    all_chats = []
    name_to_latest = {}
    for trader in ai_traders:
        if trader.chat_history:
            # 合并并记录每个模型的最新一条
            all_chats.extend(trader.chat_history)
            name_to_latest[trader.name] = trader.chat_history[-1]
        else:
            # 若该模型从未产生对话，构造一条状态消息，确保前端可见
            acct = leverage_engine.accounts.get(trader.trader_id, {}) or {}
            pos_dict = leverage_engine.get_positions(trader.trader_id) or {}
            positions_text = ' '.join(pos_dict.keys())
            fallback = {
                'timestamp': time.time(),
                'datetime': time.strftime('%m/%d %H:%M:%S'),
                'trader': trader.name,
                'model': trader.model,
                'analysis': 'Awaiting first decision…',
                'user_prompt': '',
                'trading_decision': {'decisions': {}},
                'total_value': acct.get('total_value', 100000),
                'profit_loss_percent': acct.get('profit_loss_percent', 0),
                'cash': acct.get('cash', 100000),
                'positions': positions_text
            }
            all_chats.append(fallback)
            name_to_latest[trader.name] = fallback
    
    # 排序并裁剪
    all_chats.sort(key=lambda x: x['timestamp'], reverse=True)
    return jsonify(all_chats[:50])

@app.route('/api/edition2/history')
def api_history():
    timeframe = request.args.get('timeframe', 'all')
    return jsonify(leverage_engine.get_account_history(timeframe))

# 新闻API
@app.route('/api/edition2/news')
def api_news():
    """获取最新新闻"""
    try:
        limit = request.args.get('limit', 10, type=int)
        news = news_api.get_latest_news(limit=limit)
        return jsonify(news)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/edition2/market-sentiment')
def api_market_sentiment():
    """获取市场情绪"""
    try:
        sentiment = news_api.get_market_sentiment(limit=20)
        return jsonify(sentiment)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 统一详情路由
@app.route('/api/trader/<int:trader_id>')
@app.route('/api/edition2/trader/<int:trader_id>')
def unified_trader_detail(trader_id: int):
    try:
        current_prices = market_data.get_all_prices()
        leverage_engine.update_positions(current_prices)
    except Exception as e:
        print(f"⚠️ trader detail价格更新失败: {e}, 使用缓存数据", flush=True)

    account = leverage_engine.accounts.get(trader_id, {}) or {}
    metrics = leverage_engine.get_financial_metrics(trader_id) or {}
    positions_dict = leverage_engine.get_positions(trader_id) or {}
    positions_list = list(positions_dict.values())
    return jsonify({
        'account': account,
        'metrics': metrics,
        'positions': positions_list
    })

# ========================================
# 通用路由
# ========================================
@app.route('/robots.txt')
def robots():
    from flask import send_from_directory
    return send_from_directory('static', 'robots.txt', mimetype='text/plain')

@app.route('/sitemap.xml')
def sitemap():
    from flask import send_from_directory
    return send_from_directory('static', 'sitemap.xml', mimetype='application/xml')

@app.route('/models')
def page_models():
    return render_template('models.html')

@app.route('/models_new')
def page_models_new():
    """全新的models页面（绕过缓存）"""
    return render_template('models_new.html')

@app.route('/models/<slug>')
def page_model_detail(slug: str):
    return render_template('model_detail.html', slug=slug)

# Models API
@app.route('/api/models')
def api_models():
    """获取所有AI模型的数据"""
    try:
        models_data = []
        
        if ai_traders:
            try:
                current_prices = market_data.get_all_prices()
                leverage_engine.update_positions(current_prices)
            except Exception as e:
                print(f"⚠️ 价格更新失败: {e}", flush=True)
            
            for trader in ai_traders:
                account = leverage_engine.accounts.get(trader.trader_id, {})
                all_trades = leverage_engine.get_trades(10000)
                trader_trades = [t for t in all_trades if t.get('trader_id') == trader.trader_id]
                
                # 计算统计数据
                wins = sum(1 for t in trader_trades if t.get('pnl', 0) > 0)
                losses = sum(1 for t in trader_trades if t.get('pnl', 0) < 0)
                total_trades = len(trader_trades)
                win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
                
                biggest_win = max([t.get('pnl', 0) for t in trader_trades], default=0)
                biggest_loss = min([t.get('pnl', 0) for t in trader_trades], default=0)
                
                total_wins = sum(t.get('pnl', 0) for t in trader_trades if t.get('pnl', 0) > 0)
                total_losses = abs(sum(t.get('pnl', 0) for t in trader_trades if t.get('pnl', 0) < 0))
                profit_loss_ratio = (total_wins / total_losses) if total_losses > 0 else (total_wins if total_wins > 0 else 0)
                
                models_data.append({
                    'id': trader.trader_id,
                    'name': trader.name,
                    'edition': '2',  # 保持为'2'以兼容前端逻辑
                    'total_value': account.get('total_value', 100000),
                    'profit_loss_percent': account.get('profit_loss_percent', 0),
                    'positions': len(leverage_engine.get_positions(trader.trader_id)),
                    'trades': total_trades,
                    'win_rate': win_rate,
                    'wins': wins,
                    'losses': losses,
                    'biggest_win': biggest_win,
                    'biggest_loss': biggest_loss,
                    'profit_loss_ratio': profit_loss_ratio
                })
        
        # 按盈亏排序
        models_data.sort(key=lambda x: x['total_value'], reverse=True)
        return jsonify(models_data)
    except Exception as e:
        print(f"❌ /api/models 错误: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'models': []}), 500

@app.route('/api/model/<model_id>')
def api_model_detail(model_id: str):
    """获取单个模型的详细数据"""
    # 处理slug格式（qwen3-max, deepseek-chat-v3.1）
    slug_to_id = {
        'qwen3-max': 1,
        'deepseek-chat-v3.1': 2,
        'deepseek-v3': 2
    }
    
    # 尝试从slug转换为ID
    if model_id in slug_to_id:
        trader_id = slug_to_id[model_id]
    else:
        try:
            trader_id = int(model_id.replace('_e2', ''))  # 兼容旧的_e2后缀
        except ValueError:
            return jsonify({'error': 'Invalid model ID'}), 404
    
    # 查找trader
    trader = None
    for t in ai_traders:
        if t.trader_id == trader_id:
            trader = t
            break
    
    if not trader:
        return jsonify({'error': 'Model not found'}), 404
    
    # 获取账户信息并更新持仓（确保数据最新）
    try:
        current_prices = market_data.get_all_prices()
        leverage_engine.update_positions(current_prices)
    except Exception as e:
        print(f"⚠️ 模型详情页价格更新失败: {e}, 使用缓存数据", flush=True)
    
    account = leverage_engine.accounts.get(trader_id, {})
    positions = leverage_engine.get_positions(trader_id)
    # 过滤异常/空持仓（quantity<=0）
    try:
        positions = {sym: pos for sym, pos in positions.items() if float(pos.get('quantity', 0)) > 0}
    except Exception:
        pass
    
    # 计算总盈亏 (realized + unrealized)
    realized_pnl = account.get('realized_pnl', 0)
    unrealized_pnl = account.get('unrealized_pnl', 0)
    total_pnl_amount = realized_pnl + unrealized_pnl
    
    # 将total_pnl_amount添加到account对象中供前端使用
    account['total_pnl_amount'] = total_pnl_amount
    
    # 获取交易记录（只包含已关闭的交易）
    all_trades = leverage_engine.get_trades(1000)
    closed_trades = [t for t in all_trades if t['trader_id'] == trader_id and t.get('action', '').startswith('close_')]
    
    # 计算统计数据（基于已关闭的交易）
    wins = sum(1 for t in closed_trades if t.get('pnl', 0) > 0)
    losses = sum(1 for t in closed_trades if t.get('pnl', 0) < 0)
    total_trades = len(closed_trades)
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
    
    biggest_win = max([t.get('pnl', 0) for t in closed_trades], default=0)
    biggest_loss = min([t.get('pnl', 0) for t in closed_trades], default=0)
    
    total_wins = sum(t.get('pnl', 0) for t in closed_trades if t.get('pnl', 0) > 0)
    total_losses = abs(sum(t.get('pnl', 0) for t in closed_trades if t.get('pnl', 0) < 0))
    profit_loss_ratio = (total_wins / total_losses) if total_losses > 0 else (total_wins if total_wins > 0 else 0)
    
    # 计算平均杠杆和置信度（基于已关闭的交易）
    valid_trades = [t for t in closed_trades if t.get('leverage')]
    avg_leverage = sum(t.get('leverage', 0) for t in valid_trades) / len(valid_trades) if valid_trades else 0
    
    confident_trades = [t for t in closed_trades if t.get('confidence')]
    avg_confidence = sum(t.get('confidence', 0) for t in confident_trades) / len(confident_trades) if confident_trades else 0
    
    # 统计持仓时间（基于已关闭的交易）
    long_count = sum(1 for t in closed_trades if t.get('side') == 'long')
    short_count = sum(1 for t in closed_trades if t.get('side') == 'short')
    hold_times = {
        'long': int((long_count / total_trades * 100) if total_trades > 0 else 0),
        'short': int((short_count / total_trades * 100) if total_trades > 0 else 0),
        'flat': int((100 - (long_count + short_count) / total_trades * 100) if total_trades > 0 else 100)
    }
    
    # 组合开仓和平仓交易，用于前端展示
    # 1. 当前持仓（标记为open）
    combined_trades = []
    for symbol, pos in positions.items():
        combined_trades.append({
            'status': 'open',
            'side': pos.get('side', 'long'),
            'symbol': symbol,
            'entry_time': pos.get('entry_time', 0),
            'exit_time': None,
            'entry_price': pos.get('entry_price', 0),
            'exit_price': pos.get('current_price', 0),
            'quantity': pos.get('quantity', 0),
            'holding_time': int(time.time() - pos.get('entry_time', time.time())),
            'net_pnl': pos.get('unrealized_pnl', 0),
            'leverage': pos.get('leverage', 1)
        })
    
    # 2. 已关闭的交易
    for t in closed_trades[-50:]:  # 最近50笔已关闭交易
        combined_trades.append({
            'status': 'closed',
            'side': t.get('side', 'long'),
            'symbol': t.get('symbol', ''),
            'entry_time': t.get('entry_time', 0),
            'exit_time': t.get('exit_time', 0),
            'entry_price': t.get('entry_price', 0),
            'exit_price': t.get('exit_price', 0),
            'quantity': t.get('quantity', 0),
            'holding_time': t.get('holding_seconds', 0),
            'net_pnl': t.get('pnl', 0),
            'leverage': t.get('leverage', 1)
        })
    
    # 按时间排序（最新的在前）
    combined_trades.sort(key=lambda x: x['entry_time'], reverse=True)
    
    return jsonify({
        'id': model_id,
        'name': trader.name,
        'edition': '2',  # 保持为'2'以兼容前端逻辑
        'model': trader.model,
        'strategy': trader.strategy,
        'account': account,
        'positions': list(positions.values()),  # 转换为列表（已过滤零数量）
        'trades': combined_trades[:100],  # 合并后的交易记录（含开仓+平仓）
        'last_trades': combined_trades[:100],  # 兼容前端的字段名
        'chat_history': trader.chat_history[-20:],  # 最近20条分析
        'stats': {
            'win_rate': win_rate,
            'total_trades': total_trades,
            'wins': wins,
            'losses': losses,
            'biggest_win': biggest_win,
            'biggest_loss': biggest_loss,
            'profit_loss_ratio': profit_loss_ratio,
            'avg_leverage': avg_leverage,
            'avg_confidence': avg_confidence,
            'hold_times': hold_times
        }
    })

# ========================================
# WebSocket事件
# ========================================
@socketio.on('connect')
def handle_connect():
    emit('system_status', {
        'system_running': system_running
    })

# ========================================
# 系统初始化（在模块加载时执行）
# ========================================
def init_trading_system():
    """初始化并启动交易系统"""
    global system_running
    
    print("\n" + "="*70, flush=True)
    print("🎯 Trigo Nexus - Edition 1 (带新闻功能)", flush=True)
    print("="*70, flush=True)
    
    # 初始化交易员
    initialize_traders()
    
    # 🔧 修复历史数据：同步 margin_used
    print("\n🔧 检查并修复 margin_used...", flush=True)
    try:
        leverage_engine.fix_margin_used_all()
    except Exception as e:
        print(f"⚠️ margin_used 修复出错: {e}", flush=True)
    
    # 启动交易循环
    system_running = True
    threading.Thread(target=trading_loop, daemon=True).start()
    
    print("\n" + "="*70, flush=True)
    print("✅ 系统已启动", flush=True)
    print("="*70, flush=True)
    print(f"📍 主页: /", flush=True)
    print("="*70 + "\n", flush=True)

# 自动启动交易系统（无论是直接运行还是通过WSGI）
init_trading_system()

# ========================================
# 开发环境直接运行
# ========================================
if __name__ == '__main__':
    # 启动Flask服务
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5001))
    
    socketio.run(app, host=host, port=port, debug=False, allow_unsafe_werkzeug=True)

