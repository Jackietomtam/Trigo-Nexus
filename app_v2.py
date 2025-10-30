"""
Alpha Arena - 完整杠杆交易系统
集成所有新模块
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import threading
import time
import os

# 导入所有模块
from market_data import MarketData
from kline_data import KLineData
from leverage_engine import LeverageEngine
from order_manager import OrderManager
from ai_trader_v2 import AITraderV2
from config import INITIAL_BALANCE, TRADING_INTERVAL, AI_MODELS

app = Flask(__name__)
app.config['SECRET_KEY'] = 'alpha-arena-secret-key'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# 初始化系统
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

# 模型slug映射（用于 /models/<slug> 详情页）
MODEL_SLUGS = {
    'qwen3-max': 1,
    'deepseek-chat-v3.1': 2,
    'deepseek-v3': 2
}

def initialize_traders():
    """初始化AI交易员"""
    global ai_traders
    ai_traders = []
    
    for model_config in AI_MODELS:
        trader_id = model_config['id']
        leverage_engine.create_account(trader_id, model_config['name'])
        
        trader = AITraderV2(
            trader_id=trader_id,
            name=model_config['name'],
            strategy=model_config['strategy'],
            model=model_config['model'],
            leverage_engine=leverage_engine,
            kline_data=kline_data,
            order_manager=order_manager
        )
        ai_traders.append(trader)
        print(f"  ✓ {model_config['name']} ({model_config['model']})")
    
    print(f"\n✓ 已初始化 {len(ai_traders)} 个AI交易员")

def trading_loop():
    """交易主循环"""
    global system_running, competition_stats
    
    print("🚀 杠杆交易系统启动...", flush=True)
    competition_stats['start_time'] = time.time()
    
    while system_running:
        try:
            print(f"\n⏰ 交易周期 #{competition_stats['invocations']}", flush=True)
            competition_stats['invocations'] += 1
            
            # 更新K线数据
            kline_data.update_klines()
            print(f"📊 K线数据已更新", flush=True)
            
            # 获取当前价格
            current_prices = market_data.get_all_prices()
            
            # 更新持仓
            leverage_engine.update_positions(current_prices)
            print(f"💰 持仓已更新", flush=True)
            
            # 检查止损止盈
            triggered = order_manager.check_orders(current_prices)
            if triggered:
                print(f"⚡ 触发{len(triggered)}个订单", flush=True)
            
            # AI决策
            print(f"🤖 开始AI决策...", flush=True)
            for trader in ai_traders:
                result = trader.make_decision()
                if result and result.get('success'):
                    competition_stats['total_trades'] += 1
                    action = result.get('trade', {}).get('action', '')
                    symbol = result.get('trade', {}).get('symbol', '')
                    print(f"✓ {trader.name}: {action} {symbol}", flush=True)
            
            # 推送更新到前端
            price_changes = {}
            for sym in current_prices.keys():
                price_changes[sym] = market_data.get_price_change(sym)
            
            socketio.emit('market_update', {
                'prices': current_prices,
                'changes': price_changes,
                'leaderboard': leverage_engine.get_leaderboard(),
                'trades': leverage_engine.get_trades(100),
                'history': leverage_engine.get_account_history(),
                'stats': competition_stats
            })
            
            time.sleep(TRADING_INTERVAL)
            
        except Exception as e:
            print(f"交易循环错误: {e}", flush=True)
            import traceback
            traceback.print_exc()
            time.sleep(5)

# API路由
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/robots.txt')
def robots():
    """Serve robots.txt for SEO"""
    from flask import send_from_directory
    return send_from_directory('static', 'robots.txt', mimetype='text/plain')

@app.route('/sitemap.xml')
def sitemap():
    """Serve sitemap.xml for SEO"""
    from flask import send_from_directory
    return send_from_directory('static', 'sitemap.xml', mimetype='application/xml')

@app.route('/leaderboard')
def page_leaderboard():
    return render_template('index.html')

@app.route('/models')
def page_models():
    return render_template('index.html')

@app.route('/models/<slug>')
def page_model_detail(slug: str):
    return render_template('model_detail.html', slug=slug)

@app.route('/api/prices')
def get_prices():
    prices = market_data.get_all_prices()
    changes = {sym: market_data.get_price_change(sym) for sym in prices.keys()}
    return jsonify({'prices': prices, 'changes': changes})

@app.route('/api/leaderboard')
def get_leaderboard():
    current_prices = market_data.get_all_prices()
    leverage_engine.update_positions(current_prices)
    return jsonify(leverage_engine.get_leaderboard())

@app.route('/api/leaderboard_full')
def get_leaderboard_full():
    """完整排行榜统计"""
    lb = leverage_engine.get_leaderboard()
    full = []
    for acc in lb:
        total_trades = acc['wins'] + acc['losses']
        win_rate = (acc['wins'] / total_trades * 100) if total_trades > 0 else 0
        sharpe = 0.5 if acc['profit_loss_percent'] > 0 else -0.3  # 简化Sharpe
        
        full.append({
            'rank': acc['rank'],
            'model': acc['name'],
            'acct_value': acc['total_value'],
            'return_percent': acc['profit_loss_percent'],
            'total_pnl': acc['realized_pnl'],
            'fees': acc['fees'],
            'win_rate': win_rate,
            'biggest_win': acc['biggest_win'],
            'biggest_loss': acc['biggest_loss'],
            'sharpe': sharpe,
            'trades': acc['trades_count']
        })
    return jsonify(full)

@app.route('/api/trades')
def get_trades():
    return jsonify(leverage_engine.get_trades(100))

@app.route('/api/chat')
def get_chat():
    all_chats = []
    for trader in ai_traders:
        all_chats.extend(trader.chat_history)
    all_chats.sort(key=lambda x: x['timestamp'], reverse=True)
    return jsonify(all_chats[:50])

@app.route('/api/history')
def get_history():
    """获取账户价值历史"""
    timeframe = request.args.get('timeframe', 'all')
    return jsonify(leverage_engine.get_account_history(timeframe))

@app.route('/api/trader/<int:trader_id>')
def get_trader(trader_id):
    # 更新价格
    current_prices = market_data.get_all_prices()
    leverage_engine.update_positions(current_prices)
    
    # 使用统一的财务指标
    metrics = leverage_engine.get_financial_metrics(trader_id)
    if not metrics:
        return jsonify({'error': 'Trader not found'}), 404
    
    return jsonify({
        'metrics': metrics,
        # 兼容旧格式
        'account': {
            'name': metrics['trader_name'],
            'total_value': metrics['total_value'],
            'cash': metrics['available_cash'],
            'unrealized_pnl': metrics['unrealized_pnl'],
            'total_pnl_amount': metrics['total_pnl_amount'],
            'total_pnl_percent': metrics['total_pnl_percent'],
        },
        'positions': metrics['positions']
    })

@app.route('/api/model/<slug>')
def get_model_detail(slug):
    """模型详情：账户概览、统计、持仓、最近交易 - 使用统一财务指标"""
    trader_id = MODEL_SLUGS.get(slug)
    if not trader_id:
        return jsonify({'error': 'model_not_found'}), 404

    # 更新价格
    current_prices = market_data.get_all_prices()
    leverage_engine.update_positions(current_prices)
    
    # 使用统一的财务指标
    metrics = leverage_engine.get_financial_metrics(trader_id)
    if not metrics:
        return jsonify({'error': 'model_not_found'}), 404

    # 基础统计
    avg_leverage = 0.0
    avg_confidence = 0.0
    if metrics['positions']:
        levs = [p['leverage'] for p in metrics['positions']]
        confs = [p.get('confidence', 0.0) for p in metrics['positions']]
        avg_leverage = sum(levs) / len(levs)
        avg_confidence = sum(confs) / len(confs) if confs else 0.0

    # 持仓明细（已包含在metrics中）
    positions_detail = metrics['positions']
    positions = leverage_engine.get_positions(trader_id)  # 仍需要原始positions用于trades逻辑

    # 最近交易（仅该模型）
    trades = [t for t in leverage_engine.get_trades(200) if t['trader_id'] == trader_id]
    # 计算持仓时长、费用等（针对close_交易）
    result_trades = []
    
    # 1. 已关闭的交易
    for t in trades:
        if not t['action'].startswith('close_'):
            continue
        open_ts = None
        # 找最近一次对应open
        for ot in reversed(trades):
            if ot['action'].startswith('open_') and ot['symbol'] == t['symbol'] and ot['timestamp'] < t['timestamp']:
                open_ts = ot['timestamp']
                break
        holding_seconds = int(t['timestamp'] - open_ts) if open_ts else 0
        qty = t.get('quantity', 0)
        entry_price = t.get('entry_price', 0)
        exit_price = t.get('exit_price', 0)
        notional_entry = qty * entry_price
        notional_exit = qty * exit_price
        total_fees = notional_entry * 0.001 + notional_exit * 0.001
        result_trades.append({
            'side': 'long' if t['side'] == 'long' else 'short',
            'symbol': t['symbol'],
            'entry_price': entry_price,
            'exit_price': exit_price,
            'quantity': qty,
            'holding_time': holding_seconds,
            'entry_time': open_ts,
            'exit_time': t['timestamp'],
            'notional_entry': notional_entry,
            'notional_exit': notional_exit,
            'total_fees': total_fees,
            'net_pnl': t.get('pnl', 0),
            'status': 'closed'
        })
    
    # 2. 活跃持仓（作为进行中的交易）
    for sym, pos in positions.items():
        # 找到对应的开仓记录
        open_trade = None
        for ot in reversed(trades):
            if ot['action'].startswith('open_') and ot['symbol'] == sym:
                open_trade = ot
                break
        
        if open_trade:
            qty = pos['quantity']
            entry_price = pos['entry_price']
            current_price = pos['current_price']
            entry_time = pos.get('entry_time', open_trade['timestamp'])
            holding_seconds = int(time.time() - entry_time)
            notional_entry = qty * entry_price
            notional_current = qty * current_price
            entry_fee = notional_entry * 0.001
            
            result_trades.append({
                'side': pos['side'],
                'symbol': sym,
                'entry_price': entry_price,
                'exit_price': current_price,  # 当前价格
                'quantity': qty,
                'holding_time': holding_seconds,
                'entry_time': entry_time,
                'exit_time': None,  # 未平仓
                'notional_entry': notional_entry,
                'notional_exit': notional_current,
                'total_fees': entry_fee,  # 只有开仓费用
                'net_pnl': pos['unrealized_pnl'],
                'status': 'open'
            })
    
    # 按时间倒序排序
    result_trades.sort(key=lambda x: x.get('entry_time', 0), reverse=True)
    result_trades = result_trades[:25]

    # long/short/flat 比例（基于已关闭交易数）
    closed = [t for t in trades if t['action'].startswith('close_')]
    total_closed = max(1, len(closed))
    long_count = len([t for t in closed if t['side'] == 'long'])
    short_count = len(closed) - long_count
    hold_times = {
        'long': round(long_count / total_closed * 100, 1),
        'short': round(short_count / total_closed * 100, 1),
        'flat': round(100 - (long_count + short_count) / total_closed * 100, 1)
    }

    return jsonify({
        'account': {
            'name': metrics['trader_name'],
            'total_value': metrics['total_value'],
            'cash': metrics['available_cash'],
            'unrealized_pnl': metrics['unrealized_pnl'],
            'realized_pnl': metrics['realized_pnl'],
            'fees': metrics['total_fees'],
            'total_pnl_amount': metrics['total_pnl_amount'],
            'total_pnl_percent': metrics['total_pnl_percent'],
            'biggest_win': metrics['biggest_win'],
            'biggest_loss': metrics['biggest_loss'],
        },
        'stats': {
            'avg_leverage': avg_leverage,
            'avg_confidence': avg_confidence,
            'biggest_win': metrics['biggest_win'],
            'biggest_loss': metrics['biggest_loss'],
            'total_fees': metrics['total_fees'],
            'net_realized': metrics['realized_pnl'],
            'hold_times': hold_times
        },
        'positions': positions_detail,
        'last_trades': result_trades,
        'metrics': metrics  # 完整的财务指标
    })

@app.route('/api/status')
def get_status():
    return jsonify({
        'running': system_running,
        'traders_count': len(ai_traders),
        'stats': competition_stats
    })

@app.route('/api/start')
def start_competition():
    global system_running
    
    if not system_running:
        system_running = True
        print("⚡ 启动交易线程...", flush=True)
        thread = threading.Thread(target=trading_loop)
        thread.daemon = True
        thread.start()
        return jsonify({'status': 'started'})
    else:
        return jsonify({'status': 'already_running'})

@app.route('/api/stop')
def stop_competition():
    global system_running
    system_running = False
    return jsonify({'status': 'stopped'})

@app.route('/api/reset')
def reset_competition():
    global system_running, competition_stats
    system_running = False
    time.sleep(2)
    
    leverage_engine.__init__(INITIAL_BALANCE)
    kline_data.__init__(market_data)
    initialize_traders()
    
    competition_stats = {'start_time': None, 'total_trades': 0, 'invocations': 0}
    return jsonify({'status': 'reset'})

# WebSocket事件
@socketio.on('connect')
def handle_connect():
    print('客户端已连接')
    emit('connection_response', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    print('客户端已断开')

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Alpha Arena - 杠杆交易竞赛系统")
    print("=" * 60)
    
    initialize_traders()
    
    print("\n🌐 服务器启动在 http://localhost:5001")
    print("📊 完整的技术指标和杠杆交易支持\n")
    
    # 自动启动交易循环
    system_running = True
    print("⚡ 自动启动交易线程...", flush=True)
    thread = threading.Thread(target=trading_loop)
    thread.daemon = True
    thread.start()
    
    # 支持云平台部署：从环境变量读取端口，绑定到 0.0.0.0
    port = int(os.getenv('PORT', 5001))
    host = os.getenv('HOST', '0.0.0.0')
    socketio.run(app, host=host, port=port, debug=False, allow_unsafe_werkzeug=True)

