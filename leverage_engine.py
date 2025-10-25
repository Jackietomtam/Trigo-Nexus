"""
杠杆交易引擎
支持永续合约、清算价格、止损止盈
"""

import time
from datetime import datetime

class LeverageEngine:
    """杠杆交易引擎"""
    
    def __init__(self, initial_balance=10000):
        self.accounts = {}
        self.positions = {}  # {trader_id: {symbol: position_obj}}
        self.orders = {}  # {trader_id: [order_list]}
        self.trades = []
        self.initial_balance = initial_balance
        self.account_history = {}
        
        # BTC Buy & Hold 基准
        self.btc_benchmark = {
            'initial_price': None,
            'initial_time': time.time(),
            'history': []
        }
        
    def create_account(self, trader_id, trader_name):
        """创建交易账户"""
        self.accounts[trader_id] = {
            'id': trader_id,
            'name': trader_name,
            'cash': self.initial_balance,
            'margin_used': 0,
            'total_value': self.initial_balance,
            'unrealized_pnl': 0,
            'realized_pnl': 0,
            'profit_loss_percent': 0,
            'fees': 0,
            'wins': 0,
            'losses': 0,
            'biggest_win': 0,
            'biggest_loss': 0,
            'trades_count': 0,
            'returns': [],
            'created_at': time.time()
        }
        self.positions[trader_id] = {}
        self.orders[trader_id] = []
        self.account_history[trader_id] = []
        return self.accounts[trader_id]
    
    def open_position(self, trader_id, symbol, side, quantity, price, leverage, 
                     profit_target=None, stop_loss=None, invalidation_condition=None, 
                     confidence=0.5, risk_usd=0, reason=""):
        """
        开仓
        side: 'long' 或 'short'
        leverage: 杠杆倍数 (5-40)
        """
        if trader_id not in self.accounts:
            return {'success': False, 'error': '账户不存在'}
        
        account = self.accounts[trader_id]
        
        # 计算所需保证金
        notional = quantity * price
        margin_required = notional / leverage
        fee = notional * 0.001  # 0.1% 手续费
        
        # 检查可用资金
        available = account['cash'] - account['margin_used']
        if margin_required + fee > available:
            return {'success': False, 'error': '保证金不足'}
        
        # 计算清算价格
        if side == 'long':
            # 多仓清算价 = 入场价 * (1 - 1/leverage)
            liquidation_price = price * (1 - 0.95 / leverage)
        else:
            # 空仓清算价 = 入场价 * (1 + 1/leverage)
            liquidation_price = price * (1 + 0.95 / leverage)
        
        # 创建持仓
        position = {
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'entry_price': price,
            'current_price': price,
            'leverage': leverage,
            'margin': margin_required,
            'liquidation_price': liquidation_price,
            'unrealized_pnl': 0,
            'profit_target': profit_target,
            'stop_loss': stop_loss,
            'invalidation_condition': invalidation_condition,
            'confidence': confidence,
            'risk_usd': risk_usd,
            'entry_time': time.time(),
            'notional_usd': notional
        }
        
        # 更新账户：按保证金账户口径，开仓只扣手续费，保证金计入 margin_used（不减少cash），权益不变
        account['cash'] -= fee
        account['margin_used'] += margin_required
        account['fees'] += fee
        
        # 保存持仓
        if trader_id not in self.positions:
            self.positions[trader_id] = {}
        self.positions[trader_id][symbol] = position
        
        # 记录交易
        trade = {
            'id': len(self.trades) + 1,
            'trader_id': trader_id,
            'trader_name': account['name'],
            'symbol': symbol,
            'action': 'open_' + side,
            'side': side,
            'quantity': quantity,
            'price': price,
            'leverage': leverage,
            'notional': notional,
            'margin': margin_required,
            'timestamp': time.time(),
            'datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'reason': reason
        }
        self.trades.append(trade)
        account['trades_count'] += 1
        
        return {'success': True, 'trade': trade, 'position': position}
    
    def close_position(self, trader_id, symbol, current_price, reason=""):
        """平仓"""
        if trader_id not in self.positions or symbol not in self.positions[trader_id]:
            return {'success': False, 'error': '持仓不存在'}
        
        account = self.accounts[trader_id]
        position = self.positions[trader_id][symbol]
        
        # 计算盈亏
        if position['side'] == 'long':
            pnl = (current_price - position['entry_price']) * position['quantity']
        else:  # short
            pnl = (position['entry_price'] - current_price) * position['quantity']
        
        # 手续费
        notional = position['quantity'] * current_price
        fee = notional * 0.001
        
        # 净盈亏
        net_pnl = pnl - fee
        
        # 更新账户：平仓增加净盈亏，释放保证金（不影响cash）
        account['cash'] += net_pnl
        account['margin_used'] -= position['margin']
        account['realized_pnl'] += net_pnl
        account['fees'] += fee
        
        # 统计
        if net_pnl >= 0:
            account['wins'] += 1
            if net_pnl > account['biggest_win']:
                account['biggest_win'] = net_pnl
        else:
            account['losses'] += 1
            if net_pnl < account['biggest_loss']:
                account['biggest_loss'] = net_pnl
        
        # 记录交易
        entry_time = position.get('entry_time', time.time())
        exit_time = time.time()
        holding_seconds = int(exit_time - entry_time)
        
        trade = {
            'id': len(self.trades) + 1,
            'trader_id': trader_id,
            'trader_name': account['name'],
            'symbol': symbol,
            'action': 'close_' + position['side'],
            'side': position['side'],
            'quantity': position['quantity'],
            'entry_price': position['entry_price'],
            'exit_price': current_price,
            'pnl': net_pnl,
            'leverage': position['leverage'],
            'entry_time': entry_time,
            'exit_time': exit_time,
            'entry_datetime': datetime.fromtimestamp(entry_time).strftime('%Y-%m-%d %H:%M:%S'),
            'exit_datetime': datetime.fromtimestamp(exit_time).strftime('%Y-%m-%d %H:%M:%S'),
            'holding_seconds': holding_seconds,
            'timestamp': exit_time,
            'datetime': datetime.fromtimestamp(exit_time).strftime('%Y-%m-%d %H:%M:%S'),
            'reason': reason
        }
        self.trades.append(trade)
        
        # 删除持仓
        del self.positions[trader_id][symbol]
        
        return {'success': True, 'trade': trade, 'pnl': net_pnl}
    
    def update_positions(self, current_prices):
        """更新所有持仓的未实现盈亏"""
        for trader_id, positions in self.positions.items():
            total_unrealized = 0
            
            for symbol, pos in positions.items():
                if symbol in current_prices:
                    current_price = current_prices[symbol]
                    pos['current_price'] = current_price
                    
                    # 计算未实现盈亏
                    if pos['side'] == 'long':
                        unrealized = (current_price - pos['entry_price']) * pos['quantity']
                    else:
                        unrealized = (pos['entry_price'] - current_price) * pos['quantity']
                    
                    pos['unrealized_pnl'] = unrealized
                    total_unrealized += unrealized
                    
                    # 检查是否触及清算价
                    if pos['side'] == 'long' and current_price <= pos['liquidation_price']:
                        self.liquidate_position(trader_id, symbol, current_price)
                    elif pos['side'] == 'short' and current_price >= pos['liquidation_price']:
                        self.liquidate_position(trader_id, symbol, current_price)
            
            # 更新账户总价值（权益 = 初始资金 + 已实现盈亏 + 未实现盈亏 - 手续费）
            account = self.accounts[trader_id]
            account['unrealized_pnl'] = total_unrealized
            # 正确的计算：总价值 = 初始资金 - 已付手续费 + 盈亏
            account['total_value'] = self.initial_balance - account['fees'] + account['realized_pnl'] + total_unrealized
            account['profit_loss_percent'] = ((account['total_value'] - self.initial_balance) / self.initial_balance) * 100
            
            # 记录历史（每次持仓更新都记录，确保曲线反映市场波动）
            import time
            if trader_id not in self.account_history:
                self.account_history[trader_id] = []
            
            ts = time.time()
            # 强制每次追加新点，展现真实波动
            self.account_history[trader_id].append({
                'timestamp': ts,
                'value': account['total_value'],
                'profit_loss_percent': account['profit_loss_percent']
            })
            
            # 只保留最近1000个数据点
            if len(self.account_history[trader_id]) > 1000:
                self.account_history[trader_id] = self.account_history[trader_id][-1000:]
        
        # 更新BTC Buy & Hold基准
        if 'BTC' in current_prices:
            btc_price = current_prices['BTC']
            
            # 初始化BTC基准价格
            if self.btc_benchmark['initial_price'] is None:
                self.btc_benchmark['initial_price'] = btc_price
            
            # 计算BTC Buy & Hold收益
            btc_return_pct = ((btc_price - self.btc_benchmark['initial_price']) / self.btc_benchmark['initial_price']) * 100
            btc_value = self.initial_balance * (1 + btc_return_pct / 100)
            
            # 记录历史
            self.btc_benchmark['history'].append({
                'timestamp': ts,
                'value': btc_value,
                'profit_loss_percent': btc_return_pct,
                'price': btc_price
            })
            
            # 只保留最近1000个数据点
            if len(self.btc_benchmark['history']) > 1000:
                self.btc_benchmark['history'] = self.btc_benchmark['history'][-1000:]
    
    def liquidate_position(self, trader_id, symbol, current_price):
        """清算持仓"""
        print(f"⚠️ {symbol} 触发清算！", flush=True)
        self.close_position(trader_id, symbol, current_price, reason="清算")
    
    def get_account(self, trader_id):
        """获取账户信息"""
        return self.accounts.get(trader_id)
    
    def get_financial_metrics(self, trader_id):
        """
        获取标准化财务指标（Single Source of Truth）
        所有前端显示都应该使用这个方法的返回值，确保数据一致性
        """
        account = self.accounts.get(trader_id)
        if not account:
            return None
        
        positions = self.positions.get(trader_id, {})
        
        # === 核心财务指标 ===
        initial_balance = self.initial_balance
        total_value = account['total_value']
        total_fees = account['fees']
        realized_pnl = account['realized_pnl']
        unrealized_pnl = account['unrealized_pnl']
        
        # Total P&L = 当前总价值 - 初始资金
        total_pnl_amount = total_value - initial_balance
        total_pnl_percent = (total_pnl_amount / initial_balance) * 100
        
        # === 账户概览 ===
        metrics = {
            'trader_id': trader_id,
            'trader_name': account['name'],
            
            # 核心指标
            'initial_balance': initial_balance,
            'total_value': total_value,
            'available_cash': account['cash'],
            'margin_used': account['margin_used'],
            
            # 盈亏指标
            'total_pnl_amount': total_pnl_amount,
            'total_pnl_percent': total_pnl_percent,
            'realized_pnl': realized_pnl,
            'unrealized_pnl': unrealized_pnl,
            'total_fees': total_fees,
            
            # 净值指标
            'net_profit': total_pnl_amount + total_fees,  # 净利润（扣除手续费前）
            'roi': total_pnl_percent,  # ROI = Total P&L %
            
            # 统计数据
            'trades_count': account.get('trades_count', 0),
            'wins': account.get('wins', 0),
            'losses': account.get('losses', 0),
            'biggest_win': account.get('biggest_win', 0),
            'biggest_loss': account.get('biggest_loss', 0),
        }
        
        # === 持仓详细指标 ===
        positions_metrics = []
        for symbol, pos in positions.items():
            # 计算持仓的手续费
            entry_notional = pos['quantity'] * pos['entry_price']
            entry_fee = entry_notional * 0.001
            
            # 未实现盈亏已在 pos 中
            position_metric = {
                'symbol': symbol,
                'side': pos['side'],
                'leverage': pos['leverage'],
                
                # 成本数据
                'quantity': pos['quantity'],
                'entry_price': pos['entry_price'],
                'current_price': pos['current_price'],
                'cost': entry_notional,  # 投资成本
                'margin': pos['margin'],  # 保证金
                
                # 盈亏数据
                'unrealized_pnl': pos['unrealized_pnl'],
                'entry_fee': entry_fee,  # 开仓手续费
                'market_value': pos['quantity'] * pos['current_price'],  # 当前市值
                
                # 风控数据
                'liquidation_price': pos['liquidation_price'],
                'profit_target': pos.get('profit_target', 0),
                'stop_loss': pos.get('stop_loss', 0),
                'invalidation_condition': pos.get('invalidation_condition', ''),
                
                # 元数据
                'entry_time': pos.get('entry_time'),
                'confidence': pos.get('confidence', 0),
                'risk_usd': pos.get('risk_usd', 0),
            }
            positions_metrics.append(position_metric)
        
        metrics['positions'] = positions_metrics
        
        return metrics
    
    def get_positions(self, trader_id):
        """获取持仓"""
        return self.positions.get(trader_id, {})
    
    def get_leaderboard(self):
        """获取排行榜（包含BTC基准）- 使用统一财务指标"""
        lb = []
        
        # 为每个交易员添加标准化财务指标
        for trader_id in self.accounts.keys():
            metrics = self.get_financial_metrics(trader_id)
            if metrics:
                # 转换为排行榜格式（兼容旧格式）
                lb_entry = {
                    'id': metrics['trader_id'],
                    'name': metrics['trader_name'],
                    'total_value': metrics['total_value'],
                    'profit_loss_percent': metrics['total_pnl_percent'],
                    
                    # 新增：统一的财务指标
                    'total_pnl_amount': metrics['total_pnl_amount'],
                    'unrealized_pnl': metrics['unrealized_pnl'],
                    'realized_pnl': metrics['realized_pnl'],
                    'total_fees': metrics['total_fees'],
                    'cash': metrics['available_cash'],
                    'margin_used': metrics['margin_used'],
                    
                    # 统计数据
                    'trades_count': metrics['trades_count'],
                    'wins': metrics['wins'],
                    'losses': metrics['losses'],
                    'biggest_win': metrics['biggest_win'],
                    'biggest_loss': metrics['biggest_loss'],
                }
                lb.append(lb_entry)
        
        # 添加BTC Buy & Hold虚拟账户
        if self.btc_benchmark['history']:
            latest = self.btc_benchmark['history'][-1]
            btc_pnl_amount = latest['value'] - self.initial_balance
            btc_account = {
                'id': 999,
                'name': 'BTC BUY&HOLD',
                'total_value': latest['value'],
                'profit_loss_percent': latest['profit_loss_percent'],
                'total_pnl_amount': btc_pnl_amount,
                'cash': 0,
                'margin_used': 0,
                'unrealized_pnl': 0,
                'realized_pnl': 0,
                'fees': 0,
                'wins': 0,
                'losses': 0,
                'trades_count': 0
            }
            lb.append(btc_account)
        
        # 按总价值排序
        lb = sorted(lb, key=lambda x: x['total_value'], reverse=True)
        for i, acc in enumerate(lb):
            acc['rank'] = i + 1
        return lb
    
    def get_trades(self, limit=100):
        """获取交易记录"""
        return sorted(self.trades, key=lambda x: x['timestamp'], reverse=True)[:limit]
    
    def get_account_history(self, timeframe='all'):
        """获取账户价值历史（包含BTC基准）"""
        history = {}
        
        for trader_id, hist in self.account_history.items():
            account = self.accounts.get(trader_id)
            if account:
                history[account['name']] = hist
        
        # 添加BTC Buy & Hold基准
        history['BTC BUY&HOLD'] = self.btc_benchmark['history']
        
        return history

