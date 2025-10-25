"""
虚拟交易引擎
管理账户、订单执行和持仓
"""

import time
from datetime import datetime
import json

class TradingEngine:
    def __init__(self, initial_balance=100000):
        self.accounts = {}  # AI 交易员账户
        self.trades = []  # 所有交易记录
        self.initial_balance = initial_balance
        self.account_history = {}  # 账户价值历史记录
        
    def create_account(self, trader_id, trader_name):
        """创建交易账户"""
        self.accounts[trader_id] = {
            'id': trader_id,
            'name': trader_name,
            'balance': self.initial_balance,  # 美元余额
            # 持仓 {symbol: {amount: float, avg_cost: float}}
            'positions': {},
            'total_value': self.initial_balance,
            'profit_loss': 0,
            'profit_loss_percent': 0,
            'trades_count': 0,
            'win_rate': 0,
            # 统计项
            'fees': 0.0,
            'realized_pnl': 0.0,
            'wins': 0,
            'losses': 0,
            'biggest_win': 0.0,
            'biggest_loss': 0.0,
            'returns': [],  # 用于 Sharpe 计算
            'created_at': time.time()
        }
        return self.accounts[trader_id]
    
    def execute_trade(self, trader_id, symbol, action, amount, price, reason=""):
        """
        执行交易
        action: 'buy' 或 'sell'
        amount: 交易数量（加密货币数量）
        """
        if trader_id not in self.accounts:
            return {'success': False, 'error': '账户不存在'}
        
        account = self.accounts[trader_id]
        fee_rate = 0.001  # 0.1% 手续费
        
        if action == 'buy':
            cost = amount * price
            if cost > account['balance']:
                return {'success': False, 'error': '余额不足'}
            
            # 手续费与余额
            fee = cost * fee_rate
            account['fees'] += fee
            account['balance'] -= (cost + fee)
            
            # 增加持仓
            pos = account['positions'].get(symbol)
            if not pos:
                account['positions'][symbol] = {'amount': 0.0, 'avg_cost': 0.0}
                pos = account['positions'][symbol]
            new_amount = pos['amount'] + amount
            if new_amount > 0:
                # 加权平均成本
                pos['avg_cost'] = (pos['amount'] * pos['avg_cost'] + amount * price) / new_amount
            pos['amount'] = new_amount
            
        elif action == 'sell':
            # 检查是否有足够的持仓
            pos = account['positions'].get(symbol)
            current_amount = pos['amount'] if pos else 0.0
            if current_amount < amount:
                return {'success': False, 'error': '持仓不足'}
            
            # 减少持仓
            pos['amount'] = current_amount - amount
            avg_cost = pos['avg_cost'] if pos else 0.0
            if pos['amount'] <= 0:
                del account['positions'][symbol]
            
            # 增加余额
            revenue = amount * price
            fee = revenue * fee_rate
            account['fees'] += fee
            account['balance'] += (revenue - fee)

            # 计算实现盈亏
            realized = (price - avg_cost) * amount
            account['realized_pnl'] += realized
            if realized >= 0:
                account['wins'] += 1
                if realized > account['biggest_win']:
                    account['biggest_win'] = realized
            else:
                account['losses'] += 1
                if realized < account['biggest_loss']:
                    account['biggest_loss'] = realized
        
        else:
            return {'success': False, 'error': '无效的交易类型'}
        
        # 记录交易
        trade = {
            'id': len(self.trades) + 1,
            'trader_id': trader_id,
            'trader_name': account['name'],
            'symbol': symbol,
            'action': action,
            'amount': amount,
            'price': price,
            'value': amount * price,
            'timestamp': time.time(),
            'datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'reason': reason
        }
        self.trades.append(trade)
        account['trades_count'] += 1
        
        return {'success': True, 'trade': trade}
    
    def update_account_values(self, current_prices):
        """更新所有账户的总价值并记录历史"""
        current_time = time.time()
        
        for trader_id, account in self.accounts.items():
            total_value = account['balance']
            
            # 计算持仓价值
            for symbol, pos in account['positions'].items():
                amt = pos['amount'] if isinstance(pos, dict) else pos
                if symbol in current_prices:
                    total_value += amt * current_prices[symbol]
            
            account['total_value'] = total_value
            account['profit_loss'] = total_value - self.initial_balance
            account['profit_loss_percent'] = ((total_value - self.initial_balance) / self.initial_balance) * 100
            
            # 记录历史
            if trader_id not in self.account_history:
                self.account_history[trader_id] = []
            
            # 计算一次周期收益率用于 Sharpe
            prev_value = self.account_history[trader_id][-1]['value'] if self.account_history[trader_id] else self.initial_balance
            period_return = 0.0
            if prev_value > 0:
                period_return = (total_value - prev_value) / prev_value
            account['returns'].append(period_return)
            if len(account['returns']) > 2000:
                account['returns'] = account['returns'][-2000:]

            self.account_history[trader_id].append({
                'timestamp': current_time,
                'value': total_value,
                'profit_loss_percent': account['profit_loss_percent']
            })
            
            # 只保留最近1000个数据点
            if len(self.account_history[trader_id]) > 1000:
                self.account_history[trader_id] = self.account_history[trader_id][-1000:]
    
    def get_leaderboard(self):
        """获取排行榜"""
        leaderboard = sorted(
            self.accounts.values(),
            key=lambda x: x['total_value'],
            reverse=True
        )
        
        # 添加排名
        for i, account in enumerate(leaderboard):
            account['rank'] = i + 1
            
        return leaderboard
    
    def get_account(self, trader_id):
        """获取账户信息"""
        return self.accounts.get(trader_id)
    
    def get_recent_trades(self, limit=50):
        """获取最近的交易记录"""
        return sorted(self.trades, key=lambda x: x['timestamp'], reverse=True)[:limit]
    
    def get_trader_trades(self, trader_id, limit=20):
        """获取特定交易员的交易记录"""
        trader_trades = [t for t in self.trades if t['trader_id'] == trader_id]
        return sorted(trader_trades, key=lambda x: x['timestamp'], reverse=True)[:limit]
    
    def get_portfolio_summary(self, trader_id, current_prices):
        """获取投资组合摘要"""
        account = self.accounts.get(trader_id)
        if not account:
            return None
        
        positions_detail = []
        for symbol, pos in account['positions'].items():
            amt = pos['amount'] if isinstance(pos, dict) else pos
            if symbol in current_prices:
                current_price = current_prices[symbol]
                value = amt * current_price
                positions_detail.append({
                    'symbol': symbol,
                    'amount': amt,
                    'current_price': current_price,
                    'value': value
                })
        
        return {
            'account': account,
            'positions': positions_detail,
            'cash': account['balance']
        }
    
    def get_account_history(self, trader_id=None, timeframe='all'):
        """获取账户价值历史"""
        if trader_id:
            history = self.account_history.get(trader_id, [])
        else:
            # 返回所有账户的历史
            history = {}
            for tid, hist in self.account_history.items():
                account = self.accounts.get(tid)
                if account:
                    history[account['name']] = hist
            return history
        
        # 根据时间筛选
        if timeframe == '72h' and history:
            cutoff_time = time.time() - (72 * 3600)
            history = [h for h in history if h['timestamp'] >= cutoff_time]
        
        return history

    # 计算 Sharpe（基于周期收益率）
    def _compute_sharpe(self, returns):
        import math
        if not returns:
            return 0.0
        mu = sum(returns) / len(returns)
        var = sum((r - mu) ** 2 for r in returns) / len(returns) if len(returns) > 0 else 0
        sigma = math.sqrt(var) if var > 0 else 0
        if sigma == 0:
            return 0.0
        # 假设周期较短，直接乘以 sqrt(n) 做年化近似（演示用途）
        return mu / sigma * math.sqrt(len(returns))

    def get_leaderboard_full(self):
        """返回包含费用/胜率/Sharpe/最大赢亏等统计的排行榜"""
        base = self.get_leaderboard()
        enriched = []
        for acc in base:
            total_trades = acc['wins'] + acc['losses'] if ('wins' in acc and 'losses' in acc) else acc.get('trades_count', 0)
            win_rate = (acc['wins'] / total_trades * 100) if total_trades > 0 else 0.0
            sharpe = self._compute_sharpe(acc.get('returns', []))
            enriched.append({
                'rank': acc.get('rank', 0),
                'model': acc['name'],
                'acct_value': acc['total_value'],
                'return_percent': acc['profit_loss_percent'],
                'total_pnl': acc.get('realized_pnl', 0.0),
                'fees': acc.get('fees', 0.0),
                'win_rate': win_rate,
                'biggest_win': acc.get('biggest_win', 0.0),
                'biggest_loss': acc.get('biggest_loss', 0.0),
                'sharpe': sharpe,
                'trades': acc.get('trades_count', 0)
            })
        return enriched

