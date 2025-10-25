"""
AI 加密货币交易竞赛系统主应用
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import threading
import time
from market_data import MarketData
from trading_engine import TradingEngine
from ai_trader import AITrader
from config import INITIAL_BALANCE, TRADING_INTERVAL, AI_MODELS

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ai-trading-competition-secret-key'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# 初始化系统
market_data = MarketData()
trading_engine = TradingEngine(INITIAL_BALANCE)
ai_traders = []

# 全局状态
system_running = False
competition_stats = {
    'start_time': None,
    'total_trades': 0,
    'total_volume': 0
}

def initialize_traders():
    """初始化 AI 交易员 - 每个使用不同的AI模型"""
    global ai_traders
    ai_traders = []
    
    for model_config in AI_MODELS:
        trader_id = model_config['id']
        trading_engine.create_account(trader_id, model_config['name'])
        
        trader = AITrader(
            trader_id=trader_id,
            name=model_config['name'],
            strategy=model_config['strategy'],
            model=model_config['model'],  # 不同的AI模型
            personality=model_config['personality'],
            trading_engine=trading_engine,
            market_data=market_data
        )
        ai_traders.append(trader)
        print(f"  ✓ {model_config['name']} ({model_config['model']})")
    
    print(f"\n✓ 已初始化 {len(ai_traders)} 个不同的 AI 交易员")

def trading_loop():
    """交易主循环"""
    global system_running, competition_stats
    
    print("🚀 交易系统启动...", flush=True)
    competition_stats['start_time'] = time.time()
    
    while system_running:
        try:
            print(f"⏰ 交易周期开始...")
            
            # 获取当前价格
            current_prices = market_data.get_all_prices()
            print(f"📊 已获取价格，BTC: ${current_prices.get('BTC', 0):,.2f}")
            
            # 更新账户价值
            trading_engine.update_account_values(current_prices)
            print(f"💰 已更新账户价值")
            
            # 每个 AI 做决策
            print(f"🤖 开始AI决策...")
            for trader in ai_traders:
                print(f"  → {trader.name} 正在分析...")
                result = trader.make_trading_decision()
                if result and result.get('success'):
                    competition_stats['total_trades'] += 1
                    print(f"✓ {trader.name} 执行交易: {result['trade']['action']} {result['trade']['symbol']}")
                elif result:
                    print(f"⚠ {trader.name}: {result.get('error', '无操作')}")
                else:
                    print(f"⚠ {trader.name}: 决策返回None")
            
            # 获取价格变化
            price_changes = {}
            for symbol in current_prices.keys():
                price_changes[symbol] = market_data.get_price_change(symbol)
            
            # 发送更新到前端
            socketio.emit('market_update', {
                'prices': current_prices,
                'changes': price_changes,
                'leaderboard': trading_engine.get_leaderboard(),
                'recent_trades': trading_engine.get_recent_trades(100),
                'history': trading_engine.get_account_history(),
                'stats': competition_stats
            })
            
            # 等待下一个交易周期
            time.sleep(TRADING_INTERVAL)
            
        except Exception as e:
            print(f"交易循环错误: {e}")
            time.sleep(5)

# API 路由
@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/leaderboard')
def page_leaderboard():
    return render_template('index.html')

@app.route('/models')
def page_models():
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    """获取系统状态"""
    return jsonify({
        'running': system_running,
        'traders_count': len(ai_traders),
        'stats': competition_stats
    })

@app.route('/api/prices')
def get_prices():
    """获取当前价格和涨跌幅"""
    prices = market_data.get_all_prices()
    changes = {}
    for symbol in prices.keys():
        changes[symbol] = market_data.get_price_change(symbol)
    
    return jsonify({
        'prices': prices,
        'changes': changes
    })

@app.route('/api/leaderboard')
def get_leaderboard():
    """获取排行榜"""
    current_prices = market_data.get_all_prices()
    trading_engine.update_account_values(current_prices)
    leaderboard = trading_engine.get_leaderboard()
    return jsonify(leaderboard)

@app.route('/api/leaderboard_full')
def get_leaderboard_full():
    """获取包含费用/胜率/Sharpe等指标的完整排行榜"""
    current_prices = market_data.get_all_prices()
    trading_engine.update_account_values(current_prices)
    full = trading_engine.get_leaderboard_full()
    return jsonify(full)

@app.route('/api/trades')
def get_trades():
    """获取交易记录"""
    trades = trading_engine.get_recent_trades(50)
    return jsonify(trades)

@app.route('/api/trader/<int:trader_id>')
def get_trader_info(trader_id):
    """获取交易员详细信息"""
    current_prices = market_data.get_all_prices()
    portfolio = trading_engine.get_portfolio_summary(trader_id, current_prices)
    trades = trading_engine.get_trader_trades(trader_id, 20)
    
    # 获取AI的聊天历史
    chat_history = []
    for trader in ai_traders:
        if trader.trader_id == trader_id:
            chat_history = trader.chat_history
            break
    
    if portfolio:
        return jsonify({
            'portfolio': portfolio,
            'trades': trades,
            'chat_history': chat_history
        })
    else:
        return jsonify({'error': '交易员不存在'}), 404

@app.route('/api/chat')
def get_all_chat():
    """获取所有AI的聊天记录"""
    all_chats = []
    for trader in ai_traders:
        for chat in trader.chat_history:
            all_chats.append(chat)
    
    # 按时间排序
    all_chats.sort(key=lambda x: x['timestamp'], reverse=True)
    return jsonify(all_chats[:50])  # 返回最近50条

@app.route('/api/history')
def get_history():
    """获取账户价值历史"""
    timeframe = request.args.get('timeframe', 'all')
    history = trading_engine.get_account_history(timeframe=timeframe)
    return jsonify(history)

@app.route('/api/start')
def start_competition():
    """启动竞赛"""
    global system_running
    
    if not system_running:
        system_running = True
        print("⚡ 启动交易线程...", flush=True)
        # 在新线程中启动交易循环
        thread = threading.Thread(target=trading_loop)
        thread.daemon = True
        thread.start()
        print("✓ 交易线程已启动", flush=True)
        return jsonify({'status': 'started'})
    else:
        return jsonify({'status': 'already_running'})

@app.route('/api/stop')
def stop_competition():
    """停止竞赛"""
    global system_running
    system_running = False
    return jsonify({'status': 'stopped'})

@app.route('/api/reset')
def reset_competition():
    """重置竞赛"""
    global system_running, competition_stats
    
    # 停止系统
    system_running = False
    time.sleep(2)
    
    # 重新初始化
    trading_engine.__init__(INITIAL_BALANCE)
    initialize_traders()
    
    competition_stats = {
        'start_time': None,
        'total_trades': 0,
        'total_volume': 0
    }
    
    return jsonify({'status': 'reset'})

# WebSocket 事件
@socketio.on('connect')
def handle_connect():
    """客户端连接"""
    print('客户端已连接')
    emit('connection_response', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    """客户端断开"""
    print('客户端已断开')

@socketio.on('request_update')
def handle_update_request():
    """客户端请求更新"""
    current_prices = market_data.get_all_prices()
    trading_engine.update_account_values(current_prices)
    
    emit('market_update', {
        'prices': current_prices,
        'leaderboard': trading_engine.get_leaderboard(),
        'recent_trades': trading_engine.get_recent_trades(10),
        'stats': competition_stats
    })

if __name__ == '__main__':
    print("=" * 60)
    print("🤖 AI 加密货币交易竞赛系统")
    print("=" * 60)
    
    # 初始化交易员
    initialize_traders()
    
    print("\n🌐 服务器启动在 http://localhost:5001")
    print("📊 打开浏览器访问以查看竞赛\n")
    
    # 启动服务器
    socketio.run(app, host='127.0.0.1', port=5001, debug=False)

